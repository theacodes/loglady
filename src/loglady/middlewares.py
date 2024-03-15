# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime
import sys
import threading
from types import FrameType

from .types import Record


def add_timestamp(record: Record) -> Record:
    record["timestamp"] = datetime.datetime.now()  # noqa: DTZ005
    return record


def add_thread_info(record: Record) -> Record:
    current_thread = threading.current_thread()
    record["thread_id"] = current_thread.native_id
    record["thread_name"] = current_thread.name
    return record


def add_exception_and_stack_info(record: Record) -> Record:
    if record.pop("exc_info", False):
        record["exception"] = sys.exc_info()

    if record.pop("stack_info", False):
        record["stacktrace"] = _find_app_frame()

    return record


def add_call_info(record: Record) -> Record:
    frame = _find_app_frame()
    record["call_filename"] = frame.f_code.co_filename
    record["call_module"] = frame.f_globals["__name__"]
    record["call_fn"] = frame.f_code.co_qualname
    record["call_lineno"] = frame.f_lineno
    return record


def _find_app_frame(stack: FrameType | None = None, ignores=("structlog", "loglady.")) -> FrameType:
    """Finds the first frame that isn't part of the logging code"""
    if stack is None:
        # sys._getframe is faster than inspect.currentframe()
        stack = sys._getframe(1)  # pyright: ignore[reportPrivateUsage]

    f = stack
    name = f.f_globals.get("__name__") or "?"

    while any(name.startswith(i) for i in ignores):
        if f.f_back is None:
            name = "?"
            break
        f = f.f_back
        name = f.f_globals.get("__name__") or "?"

    return f
