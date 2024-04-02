# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import contextlib
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Self

from .types import Context, Relay


class Logger:
    """It's the logger! You know how to log!"""

    __slots__ = ("_relay", "_context")

    def __init__(self, *, relay: Relay, context: Context | None = None):
        """
        Loggers shouldn't be created directly, instead, use loglady.configure()
        and loglady.logger() to get an instance.
        """
        super().__init__()
        self._relay = relay
        self._context = context if context is not None else {}

    @property
    def context(self) -> Mapping[str, Any]:
        """A read-only view of the current context. Use bind() or unbind() to
        change the context."""
        return MappingProxyType(self._context)

    def bind(self, **context: Any) -> Self:
        """Create a new logger with the given context. The new logger inherits
        this logger's context."""
        ctx = self._context.copy()
        ctx.update(**context)
        return self.__class__(relay=self._relay, context=ctx)

    def unbind(self, *keys: str) -> Self:
        """Create a new logger without the given keys in the context."""
        inst = self.bind()
        for key in keys:
            inst._context.pop(key, None)
        return inst

    def prefix(self, prefix: str, **context) -> Self:
        """Shortcut for self.bind(prefix="...", ...)"""
        context["prefix"] = prefix
        return self.bind(**context)

    def log(self, msg, **record: Any) -> None:
        """You probably don't wanna call this, as it's the common log method
        used by info(), warning(), etc. I mean, you can call it, I'm a
        docstring, not a cop."""
        rec = self._context.copy()
        rec.update(**record)
        rec["msg"] = msg

        self._relay(rec)

    def trace(self, msg, **record: Any) -> None:
        """Log a debug message and include a stack trace.

        Note that middleware.add_exception_and_stack_info or a similar
        middleware must be used otherwise it won't actually add the stack info.
        """
        self.log(msg, level="debug", stack_info=True, **record)

    def debug(self, msg, **record: Any) -> None:
        """Log a debug message"""
        self.log(msg, level="debug", **record)

    def info(self, msg, **record: Any) -> None:
        """Log an info message"""
        self.log(msg, level="info", **record)

    def warning(self, msg, **record: Any) -> None:
        """Log a warning message"""
        self.log(msg, level="warning", **record)

    warn = warning

    def success(self, msg, **record: Any) -> None:
        """Log a success message"""
        self.log(msg, level="success", **record)

    def error(self, msg, **record: Any) -> None:
        """Log an error message"""
        self.log(msg, level="error", **record)

    def exception(self, msg, **record: Any) -> None:
        """Log an error message and include the current exception's traceback

        Note that middleware.add_exception_and_stack_info or a similar
        middleware must be used otherwise it won't actually add the exception
        and traceback.
        """
        self.log(msg, level="error", exc_info=True, **record)

    def catch(self, exc_types=BaseException, *, msg: str = "unexpected error", reraise: bool = False):
        @contextlib.contextmanager
        def catcher():
            try:
                yield
            except exc_types:
                self.exception(msg)
                if reraise:
                    raise

        return catcher()
