# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import contextlib
from types import FrameType


def check_for_tracebackhide(frame: FrameType) -> bool:
    """Helper for ignoring stackframes from functions that have a variable
    named __stacktracehide__ defined.

    This is adapted from pytest's TracebackEntry.ishidden
    """
    tbh = False

    # Note that f_locals and f_globals are normally dictionaries, but with
    # exec() and eval() they can be set to just about anything, so we swallow
    # all exceptions while trying this nonsense.
    with contextlib.suppress(Exception):
        for namespace in (frame.f_locals, frame.f_globals):
            tbh = namespace.get("__tracebackhide__", None)
            if tbh is not None:
                break

    if tbh and callable(tbh):
        tbh = tbh(frame)

    return tbh
