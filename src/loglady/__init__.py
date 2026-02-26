# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from .config import DEFAULT_PROCESSORS, configure
from .destinations import CaptureDestination, TextIODestination, stderr_destination
from .errors import LogladyError
from .exception_capture import CapturedException
from .logger import Logger
from .magics import (
    bind,
    catch,
    debug,
    error,
    exception,
    flush,
    info,
    log,
    logger,
    named,
    success,
    trace,
    warn,
    warning,
)
from .manager import Manager
from .processor import Processor, ProcessorError, ProcessorReturn
from .processors import add_call_info, add_thread_info, add_timestamp, fancy_prefix_icon
from .record import CompareRecord, Record
from .rich import RichConsoleDestination
from .stack_capture import CapturedFrame, CapturedStack
from .thread_capture import CapturedThreadInfo
from .thread_transport import ThreadTransport
from .warnings import LogladyWarning

__all__ = [
    "DEFAULT_PROCESSORS",
    "CaptureDestination",
    "CapturedException",
    "CapturedFrame",
    "CapturedStack",
    "CapturedThreadInfo",
    "CompareRecord",
    "Logger",
    "LogladyError",
    "LogladyWarning",
    "Manager",
    "Processor",
    "ProcessorError",
    "ProcessorReturn",
    "Record",
    "RichConsoleDestination",
    "TextIODestination",
    "ThreadTransport",
    "add_call_info",
    "add_thread_info",
    "add_timestamp",
    "bind",
    "catch",
    "configure",
    "debug",
    "error",
    "exception",
    "fancy_prefix_icon",
    "flush",
    "info",
    "log",
    "logger",
    "named",
    "stderr_destination",
    "success",
    "trace",
    "warn",
    "warning",
]
