# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from .config import DEFAULT_MIDDLEWARE, configure
from .destination import CaptureDestination, Destination, TextIODestination
from .logger import Logger
from .magics import bind, catch, debug, error, exception, flush, info, log, logger, success, trace, warn, warning
from .manager import Manager
from .middleware import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp, fancy_prefix_icon
from .rich import RichConsoleDestination
from .transport import SyncTransport, ThreadedTransport, Transport
from .types import Middleware, Record

__all__ = [
    "DEFAULT_MIDDLEWARE",
    # Types & classes
    "CaptureDestination",
    "Destination",
    "Logger",
    "Manager",
    "Middleware",
    "Record",
    "RichConsoleDestination",
    "SyncTransport",
    "TextIODestination",
    "ThreadedTransport",
    "Transport",
    # Middleware
    "add_call_info",
    "add_exception_and_stack_info",
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
    # Magics
    "logger",
    "success",
    "trace",
    "warn",
    "warning",
]
