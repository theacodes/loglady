# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import contextlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final, Self, overload, override

from .exception_capture import (
    CapturedException,
    capture_current_exception,
    capture_exception,
)
from .record import Context, Record
from .stack_capture import CapturedStack
from .types import Relay


@dataclass(slots=True, kw_only=True, frozen=True)
class Logger:
    """It's the logger! You know how to log!

    NOTE: Loggers shouldn't be created directly, instead, use `loglady.configure()` and `loglady.logger()` to get an
    instance.
    """

    _name: Final[str] = ""
    _relay: Final[Relay]
    _context: Final[Context] = field(default_factory=dict)

    #
    # Naming
    #

    @property
    def name(self) -> str:
        """The name of the logger.

        This is immutable. Use `named()` to create a new logger with a different name.
        """
        return self._name

    def named(self, name: str) -> Self:
        """Create a new logger with the given name. The new logger inherits this logger's context."""
        return self.__class__(_relay=self._relay, _context=self._context, _name=name)

    def prefixed(self, prefix: str, *, sep=".") -> Self:
        """Create a new logger with the given prefix added to the name. The new logger inherits this logger's context."""
        return self.named(f"{prefix}{sep}{self._name}" if self._name else prefix)

    def suffixed(self, suffix: str, *, sep=".") -> Self:
        """Create a new logger with the given suffix added to the name. The new logger inherits this logger's context."""
        return self.named(f"{self._name}{sep}{suffix}" if self._name else suffix)

    #
    # Context
    #

    @property
    def context(self) -> Mapping[str, Any]:
        """A read-only view of the current context. Use bind() or unbind() to change the context."""
        return MappingProxyType(self._context)

    def bind(self, **context: Any) -> Self:
        """Create a new logger with the given context. The new logger inherits this logger's context."""
        if context is self.context or self.context == context == {}:
            return self

        ctx = self._context.copy()
        ctx.update(**context)
        return self.__class__(_relay=self._relay, _context=ctx)

    def unbind(self, *keys: str) -> Self:
        """Create a new logger without the given keys in the context."""
        inst = self.bind()
        for key in keys:
            inst._context.pop(key, None)
        return inst

    #
    # Helpers
    #

    def create_record(self, message: str, /, level: str | None = None, **context: Any) -> Record:
        """Creates a new record without relaying it.

        You shouldn't need to call this directly, it's used by `log()` and friends.
        """
        ctx = {**self._context, **context}

        return Record(
            message=message,
            name=self._name,
            level=level,
            context=ctx,
        )

    def relay(self, record: Record) -> None:
        """Relays a precreate Record.

        You probably don't wanna call this directly, it's used by `log()` and friends. However, if you need to
        manipulate a record before sending it, this could be useful."""
        self._relay(record)

    #
    # Logging methods
    #

    def log(self, message: str, /, level: str | None = None, **context: Any) -> None:
        """You probably don't wanna call this, as it's the common log method used by info(), warning(), etc. I mean,
        you can call it, I'm a docstring, not a cop."""
        self._relay(self.create_record(message, level=level, **context))

    def trace(
        self,
        message: str,
        /,
        *,
        level: str = "debug",
        show_lines: bool = True,
        show_locals: bool = False,
        **context: Any,
    ) -> None:
        """Log a message and include a stack trace."""
        record = self.create_record(message, level=level, **context)

        record.stack = CapturedStack.create_from_caller(
            capture_lines=show_lines,
            capture_locals=show_locals,
        )

        self._relay(record)

    def debug(self, message: str, **context: Any) -> None:
        """Log a debug message"""
        self.log(message, level="debug", **context)

    def info(self, message: str, **context: Any) -> None:
        """Log an info message"""
        self.log(message, level="info", **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message"""
        self.log(message, level="warning", **context)

    warn = warning

    def success(self, message: str, **context: Any) -> None:
        """Log a success message"""
        self.log(message, level="success", **context)

    def error(self, message: str, **context: Any) -> None:
        """Log an error message"""
        self.log(message, level="error", **context)

    @overload
    def exception(
        self,
        err: BaseException | CapturedException | None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **context: Any,
    ) -> None: ...

    @overload
    def exception(
        self,
        message: str,
        err: BaseException | CapturedException | None = None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **context: Any,
    ) -> None: ...

    @overload
    def exception(
        self,
        message_or_err: str | BaseException | CapturedException | None = None,
        err_or_unspecified: BaseException | CapturedException | None = None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **context: Any,
    ) -> None: ...

    def exception(
        self,
        message_or_err: str | BaseException | CapturedException | None = None,
        err_or_unspecified: BaseException | CapturedException | None = None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **context: Any,
    ) -> None:
        """Log an error message and include exception information."""

        match message_or_err:
            case None:
                message = ""
            case str():
                message = message_or_err
            case BaseException() | CapturedException():
                message = ""
                err_or_unspecified = message_or_err

        match err_or_unspecified:
            case None:
                err = capture_current_exception(
                    capture_lines=show_lines,
                    capture_locals=show_locals,
                )
            case _:
                err = capture_exception(
                    err_or_unspecified,
                    capture_lines=show_lines,
                    capture_locals=show_locals,
                )

        record = self.create_record(message, level="error", **context)
        record.exception = err

        self._relay(record)

    def catch(self, exc_types=BaseException, *, message: str = "unexpected error", reraise: bool = False):
        @contextlib.contextmanager
        def catcher():
            try:
                yield
            except exc_types as err:
                self.exception(message, err)
                if reraise:
                    raise

        return catcher()

    @override
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self._name} context={dict(self.context)!r}>"

    def __rich_repr__(self):
        yield "context", dict(self.context)

    __rich_repr__.angular = True  # pyright: ignore[reportFunctionMemberAccess]
