# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Global state stack management.

LogLady's magics (the top-level loglady.info, etc.) need to have access to the
manager created from calling configure(), this manages keeping track of that
global state. It's done as a stack to make life easier for tests, as this allows
multiple calls to configure() to not stomp on each other.
"""

import atexit
import contextlib
from dataclasses import dataclass

from .logger import Logger
from .manager import Manager


@dataclass
class GlobalState:
    manager: Manager
    """The manager created via configure() or configure_for_tests()"""

    logger: Logger | None = None
    """The root logger used by magics"""


_STATE_STACK = []


def top() -> GlobalState | None:
    """Returns the currently active global config or None if LogLady hasn't
    been configured."""
    if not _STATE_STACK:
        return None
    return _STATE_STACK[-1]


def push(state: GlobalState):
    """Add the given state to the top of the stack, making it active."""
    return _STATE_STACK.append(state)


def pop() -> GlobalState | None:
    """Remove the currently active global config from the stack and return it.

    Returns None if the stack is empty."""
    if not _STATE_STACK:
        return None
    return _STATE_STACK.pop()


@contextlib.contextmanager
def rewind():
    """A context manager that automatically rewinds the stack on exit.

    This is useful for applying temporary configuration in tests and such.
    """
    checkpoint_size = len(_STATE_STACK)
    try:
        yield
    finally:
        assert len(_STATE_STACK) >= checkpoint_size
        while len(_STATE_STACK) != checkpoint_size:
            state = pop()
            if state is not None:
                state.manager.stop()


def _on_shutdown():
    while state := pop():
        state.manager.stop()


_ = atexit.register(_on_shutdown)
