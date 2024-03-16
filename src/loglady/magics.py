# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Magics are sugary convenience methods to quickly and easy log.

Magics all work as long as configure() has been called.
"""

from typing import Any

from . import config
from .logger import Logger

_CACHE = {}


def _cached_logger() -> Logger:
    if (logger := _CACHE.get("logger")) is None:
        logger = config.manager().logger()
        _CACHE["logger"] = logger
    return logger


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
