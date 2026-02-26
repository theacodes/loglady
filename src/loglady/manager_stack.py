# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import atexit
import contextlib
from dataclasses import dataclass, field

from ._fallback import Fallback
from .logger import Logger
from .manager import Manager
from .record import Record


@dataclass(slots=True, kw_only=True, frozen=True)
class ManagerStack:
    fallback: Fallback = field(init=False, default_factory=Fallback)

    _stack: list[Manager] = field(init=False, default_factory=list)

    @property
    def current(self) -> Manager:
        if not self._stack:
            return self.fallback.manager
        return self._stack[-1]

    @property
    def has_valid_manager(self) -> bool:
        return bool(self._stack)

    def push(self, manager: Manager) -> None:
        # When the first real manager is pushed onto the stack, send all collected fallback logs to it.
        if not self.has_valid_manager:
            self.fallback.drain_to(manager)
        self._stack.append(manager)

    def pop(self) -> Manager | None:
        if len(self._stack) == 1:
            return None
        return self._stack.pop()

    def clear(self) -> None:
        self._stack.clear()

    def flush_all(self) -> None:
        self.fallback.flush()
        for manager in self._stack:
            manager.flush()

    def logger(self, name: str = "", **context) -> Logger:
        return Logger(_name=name, _send=self.relay, _context=context)

    def relay(self, record: Record) -> None:
        self.current.send(record)

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
                if (manager := self.pop()) is not None:
                    manager.flush()


_STACK = ManagerStack()


def push(manager: Manager) -> None:
    _STACK.push(manager)


def pop() -> Manager | None:
    return _STACK.pop()


def current() -> Manager:
    return _STACK.current


def has_valid_manager() -> bool:
    return _STACK.has_valid_manager


def logger(name: str = "", **context) -> Logger:
    """Returns a logger bound to the manager stack. If the current manager is changed, this logger will follow the new
    manager."""
    return _STACK.logger(name=name, **context)


def flush_all():
    _STACK.flush_all()


@contextlib.contextmanager
def rewind():
    with _STACK.rewind():
        yield


@atexit.register
def _on_shutdown():  # pyright: ignore[reportUnusedFunction]
    _STACK.flush_all()
    _STACK.clear()
    _STACK.fallback.warn_buffered()
