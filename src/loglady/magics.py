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

from . import manager_stack
from .logger import Logger


def logger(**context: Any) -> Logger:
    return manager_stack.logger(**context)


bind = logger


def log(msg, **record: Any) -> None:
    logger().log(msg, **record)


def trace(msg, **record: Any) -> None:
    return logger().trace(msg, **record)


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


def exception(msg, **record: Any) -> None:
    logger().exception(msg, **record)


def prefix(prefix: str, **context: Any) -> Logger:
    return logger().prefix(prefix, **context)


def catch(exc_types=BaseException, *, msg: str = "unexpected error", reraise: bool = False):
    return logger().catch(exc_types=exc_types, msg=msg, reraise=reraise)


def flush():
    manager_stack.flush_all()
