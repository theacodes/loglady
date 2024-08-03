# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime
import sys
import threading
from types import FrameType

from ._tracebackhide import check_for_tracebackhide
from .types import Record


def add_timestamp(record: Record) -> Record:
    """Adds the current timestamp"""
    record["timestamp"] = datetime.datetime.now()  # noqa: DTZ005
    return record


def add_thread_info(record: Record) -> Record:
    """Adds teh current thread native id and name"""
    current_thread = threading.current_thread()
    record["thread_id"] = current_thread.ident
    record["thread_name"] = current_thread.name
    return record


def add_exception_and_stack_info(record: Record) -> Record:
    """Adds the current exception info and stacktrace

    The exception info is added if record["exc_info"] is True, likewise,
    the stacktrace is added if record["stack_info"] is True.
    """
    if record.pop("exc_info", False):
        record["exception"] = sys.exc_info()

    if record.pop("stack_info", False):
        record["stacktrace"] = _find_app_frame()

    return record


def add_call_info(record: Record) -> Record:
    """Add the calling function's name, filename, module, and lineno"""
    frame = _find_app_frame()
    record["call_filename"] = frame.f_code.co_filename
    record["call_module"] = frame.f_globals["__name__"]
    record["call_fn"] = frame.f_code.co_qualname
    record["call_lineno"] = frame.f_lineno
    return record


def _find_app_frame(stack: FrameType | None = None, ignores=("loglady.")) -> FrameType:
    """Finds the first frame that isn't part of the logging code"""
    if stack is None:
        # sys._getframe is faster than inspect.currentframe()
        stack = sys._getframe(1)  # pyright: ignore[reportPrivateUsage]

    f = stack
    name = f.f_globals.get("__name__") or "?"

    while True:
        traceback_hide = check_for_tracebackhide(f)
        ignore_hide = name.startswith(ignores)

        if not (traceback_hide or ignore_hide):
            break

        if f.f_back is None:
            name = "?"
            break

        f = f.f_back
        name = f.f_globals.get("__name__") or "?"

    return f


def fancy_prefix_icon(record: Record) -> Record:
    icon = record.get("icon", None)

    match icon:
        case ">":
            icon = "➤"
        case "->":
            icon = "🡲"
        case "<-":
            icon = "🡰"
        case "o":
            icon = "●"
        case "...":
            icon = "…"
        case "v":
            icon = "✓"
        case "x":
            icon = "✗"
        case "*":
            icon = "🟊"
        case "**":
            icon = "🞷"
        case "+":
            icon = "✦"
        case "s":
            icon = "§"
        case "p":
            icon = "¶"
        case "!!":
            icon = "‼︎"
        case "!?":
            icon = "⁉︎"
        case "?!":
            icon = "⁈"
        case "??":
            icon = "⁇"
        case "<3":
            icon = "❤︎"
        case ":)":
            icon = "☺︎"
        case ":(":
            icon = "☹︎"
        case "f":
            icon = "⚑"
        case "snow":
            icon = "☃︎"
        case _:
            pass

    if icon:
        record["icon"] = icon

    return record
