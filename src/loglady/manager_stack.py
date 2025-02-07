# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import atexit
import contextlib
from typing import Literal

from ._fallback import Fallback
from .logger import Logger
from .manager import Manager
from .types import Record


class ManagerStack:
    def __init__(self, fallback_mode: Literal["buffer", "stderr", "warn", "error"] | None = None):
        super().__init__()

        self._fallback = Fallback(fallback_mode)
        self._stack: list[Manager] = []

    @property
    def current(self) -> Manager:
        if not self._stack:
            return self._fallback.manager
        return self._stack[-1]

    @property
    def has_valid_manager(self) -> bool:
        return bool(self._stack)

    def push(self, manager: Manager) -> None:
        # When the first real manager is pushed onto the stack, send all collected fallback logs to it.
        if not self.has_valid_manager:
            self._fallback.drain_to_new_manager(manager)

        self._stack.append(manager)

    def pop(self) -> Manager | None:
        if len(self._stack) == 1:
            return None
        return self._stack.pop()

    def clear(self) -> None:
        self._stack.clear()

    def flush_all(self) -> None:
        self._fallback.manager.flush()
        for manager in self._stack:
            manager.flush()

    def stop_all(self) -> None:
        for manager in self._stack:
            manager.stop()

        self._fallback.drain_remaining_to_warn()

    def logger(self, **context) -> Logger:
        return Logger(relay=self.relay, context=context)

    def relay(self, record: Record) -> None:
        self.current.relay(record)

    @contextlib.contextmanager
    def rewind(self):
        """A context manager that automatically rewinds the stack on exit.

        This is useful for applying temporary configuration in tests and such.
        """
        checkpoint_size = len(self._stack)
        try:
            yield
        finally:
            assert len(self._stack) >= checkpoint_size
            while len(self._stack) != checkpoint_size:
                manager = self.pop()
                if manager is not None:
                    manager.stop()


_DEFAULT_STACK = ManagerStack()


def push(manager: Manager) -> None:
    _DEFAULT_STACK.push(manager)


def pop() -> Manager | None:
    return _DEFAULT_STACK.pop()


def current() -> Manager:
    return _DEFAULT_STACK.current


def has_valid_manager() -> bool:
    return _DEFAULT_STACK.has_valid_manager


def logger(**context) -> Logger:
    """Returns a logger bound to the manager stack. If the current manager is changed, this logger will follow the new
    manager."""
    return _DEFAULT_STACK.logger(**context)


def flush_all():
    _DEFAULT_STACK.flush_all()


def stop_all():
    _DEFAULT_STACK.stop_all()


@contextlib.contextmanager
def rewind():
    with _DEFAULT_STACK.rewind():
        yield


@atexit.register
def _on_shutdown():  # pyright: ignore[reportUnusedFunction]
    _DEFAULT_STACK.flush_all()
    _DEFAULT_STACK.stop_all()
    _DEFAULT_STACK.clear()
