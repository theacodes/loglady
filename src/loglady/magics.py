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

from typing import Any, overload

from loglady.exception_capture import CapturedException

from . import manager_stack
from .logger import Logger

#
# Manager shortcuts
#


def flush():
    manager_stack.flush_all()


#
# Logger creation
#


def logger(name: str = "", **context: Any) -> Logger:
    return manager_stack.logger(name=name, **context)


named = logger
bind = logger


#
# Logging shortcuts
#


def log(msg, **record: Any) -> None:
    logger().log(msg, **record)


def trace(
    msg,
    /,
    *,
    level="debug",
    show_lines: bool = True,
    show_locals: bool = False,
    **record: Any,
) -> None:
    return logger().trace(msg, level=level, show_lines=show_lines, show_locals=show_locals, **record)


def debug(msg, **record: Any) -> None:
    logger().debug(msg, **record)


def warning(msg, **record: Any) -> None:
    return logger().warning(msg, **record)


warn = warning


def info(msg, **record: Any) -> None:
    logger().info(msg, **record)


def success(msg, **record: Any) -> None:
    logger().success(msg, **record)


def error(msg, **record: Any) -> None:
    logger().error(msg, **record)


@overload
def exception(
    err: BaseException | CapturedException | None,
    /,
    *,
    show_lines: bool = True,
    show_locals: bool = False,
    **record: Any,
) -> None: ...


@overload
def exception(
    msg: str,
    err: BaseException | CapturedException | None = None,
    /,
    *,
    show_lines: bool = True,
    show_locals: bool = False,
    **record: Any,
) -> None: ...


def exception(
    msg_or_err: str | BaseException | CapturedException | None = None,
    err_or_unspecified: BaseException | CapturedException | None = None,
    /,
    *,
    show_lines: bool = True,
    show_locals: bool = False,
    **record: Any,
) -> None:
    logger().exception(msg_or_err, err_or_unspecified, show_lines=show_lines, show_locals=show_locals, **record)


def catch(exc_types=BaseException, *, message: str = "unexpected error", reraise: bool = False):
    return logger().catch(exc_types=exc_types, message=message, reraise=reraise)
