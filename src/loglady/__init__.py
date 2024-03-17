# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from .config import DEFAULT_MIDDLEWARE, configure
from .destination import CaptureDestination, Destination, TextIODestination
from .logger import Logger
from .magics import bind, debug, error, exception, info, log, success, trace, warn, warning
from .manager import Manager
from .middleware import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp
from .rich import RichConsoleDestination
from .transport import SyncTransport, ThreadedTransport, Transport
from .types import Middleware, Record

__all__ = [
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
    "DEFAULT_MIDDLEWARE",
    # Magics
    "bind",
    "configure",
    "debug",
    "error",
    "exception",
    "info",
    "log",
    "success",
    "trace",
    "warn",
    "warning",
]
