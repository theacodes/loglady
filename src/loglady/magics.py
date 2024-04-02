# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Magics are sugary convenience methods to quickly and easily log to your
heart's content.

These are exposed as top-level methods on the loglady module:

    import loglady

    loglady.configure()

    loglady.info("Hello!")

Magics all work as long as configure() has been called. They match the methods
found on Logger.
"""

from typing import Any

from . import _config_stack
from .logger import Logger


def _cached_logger() -> Logger:
    state = _config_stack.top()

    if not state:
        msg = "You must call loglady.configure() before using the magic log methods."
        raise RuntimeError(msg)

    if state.logger is None:
        state.logger = state.manager.logger()

    return state.logger


def log(msg, **record: Any) -> None:
    _cached_logger().log(msg, **record)


def trace(msg, **record: Any) -> None:
    return _cached_logger().trace(msg, **record)


def debug(msg, **record: Any) -> None:
    _cached_logger().debug(msg, **record)


def warning(msg, **record: Any) -> None:
    return _cached_logger().warning(msg, **record)


warn = warning


def info(msg, **record: Any) -> None:
    _cached_logger().info(msg, **record)


def success(msg, **record: Any) -> None:
    _cached_logger().success(msg, **record)


def error(msg, **record: Any) -> None:
    _cached_logger().error(msg, **record)


def exception(msg, **record: Any) -> None:
    _cached_logger().exception(msg, **record)


def bind(**context: Any) -> Logger:
    return _cached_logger().bind(**context)


def prefix(prefix: str, **context: Any) -> Logger:
    return _cached_logger().prefix(prefix, **context)


def catch(exc_types=BaseException, *, msg: str = "unexpected error", reraise: bool = False):
    return _cached_logger().catch(exc_types=exc_types, msg=msg, reraise=reraise)


def flush():
    state = _config_stack.top()

    if not state:
        return

    state.manager.flush()
