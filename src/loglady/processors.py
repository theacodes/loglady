# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime

from .exception_capture import capture_exception
from .record import Record
from .stack_capture import CapturedFrame
from .thread_capture import CapturedThreadInfo


def eagerly_capture_exceptions(record: Record) -> Record:
    """Eagerly captures exception info for any exceptions passed into record items.

    Typically you'd use `logger.exception` to explicitly capture a single exception, but sometimes you might do
    something silly like `logger.info("hmm", err=ValueError(...))`. That's where this comes in - it will eagerly
    convert those values into `CapturedExceptions`.
    """
    for k, v in record.items():
        if isinstance(v, BaseException):
            record[k] = capture_exception(v, capture_lines=False, capture_locals=False, capture_traceback=False)

    return record


def add_timestamp(record: Record) -> Record:
    """Adds the current timestamp"""
    if record.timestamp is None:
        record.timestamp = datetime.datetime.now().astimezone(None)
    return record


def add_thread_info(record: Record) -> Record:
    """Adds the current thread native id and name"""
    if record.thread is None:
        record.thread = CapturedThreadInfo.create()
    return record


def add_call_info(record: Record) -> Record:
    """Add the calling function's name, filename, module, and lineno"""
    if record.caller is None:
        record.caller = CapturedFrame.create_from_caller()
    return record


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
