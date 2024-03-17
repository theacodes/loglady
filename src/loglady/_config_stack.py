# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import contextlib
from dataclasses import dataclass

from .logger import Logger
from .manager import Manager


@dataclass
class GlobalState:
    manager: Manager
    logger: Logger | None = None


_STATE_STACK = []


def top() -> GlobalState | None:
    if not _STATE_STACK:
        return None
    return _STATE_STACK[-1]


def push(state: GlobalState):
    return _STATE_STACK.append(state)


def pop() -> GlobalState | None:
    if not _STATE_STACK:
        return None
    return _STATE_STACK.pop()


@contextlib.contextmanager
def rewind():
    checkpoint_size = len(_STATE_STACK)
    try:
        yield
    finally:
        assert len(_STATE_STACK) >= checkpoint_size
        while len(_STATE_STACK) != checkpoint_size:
            state = pop()
            if state is not None:
                state.manager.stop()
