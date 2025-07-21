# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import contextlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Self, overload, override

from .exception_capture import (
    CapturedException,
    capture_current_exception,
    capture_exception,
)
from .stack_capture import CapturedStack
from .types import Context, Relay, ReservedKeys


@dataclass(slots=True, kw_only=True)
class Logger:
    """It's the logger! You know how to log!

    NOTE: Loggers shouldn't be created directly, instead, use `loglady.configure()` and `loglady.logger()` to get an
    instance.
    """

    _relay: Relay
    _context: Context = field(default_factory=dict)

    @property
    def context(self) -> Mapping[str, Any]:
        """A read-only view of the current context. Use bind() or unbind() to
        change the context."""
        return MappingProxyType(self._context)

    def bind(self, **context: Any) -> Self:
        """Create a new logger with the given context. The new logger inherits
        this logger's context."""
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

    def trace(
        self,
        msg,
        /,
        *,
        level="debug",
        show_lines: bool = True,
        show_locals: bool = False,
        **record: Any,
    ) -> None:
        """Log a message and include a stack trace."""
        stack = CapturedStack.create_from_caller(
            capture_lines=show_lines,
            capture_locals=show_locals,
        )
        if stack is not None:
            record[ReservedKeys.captured_stack] = stack

        self.log(msg, level=level, **record)

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

    @overload
    def exception(
        self,
        err: BaseException | CapturedException | None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **record: Any,
    ) -> None: ...

    @overload
    def exception(
        self,
        msg: str,
        err: BaseException | CapturedException | None = None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **record: Any,
    ) -> None: ...

    @overload
    def exception(
        self,
        msg_or_err: str | BaseException | CapturedException | None = None,
        err_or_unspecified: BaseException | CapturedException | None = None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **record: Any,
    ) -> None: ...

    def exception(
        self,
        msg_or_err: str | BaseException | CapturedException | None = None,
        err_or_unspecified: BaseException | CapturedException | None = None,
        /,
        *,
        show_lines: bool = True,
        show_locals: bool = False,
        **record: Any,
    ) -> None:
        """Log an error message and include exception information."""

        match msg_or_err:
            case None:
                msg = ""
            case str():
                msg = msg_or_err
            case BaseException() | CapturedException():
                msg = ""
                err_or_unspecified = msg_or_err

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

        if err is not None:
            record[ReservedKeys.captured_exception] = err

        self.log(msg, level="error", **record)

    def catch(self, exc_types=BaseException, *, msg: str = "unexpected error", reraise: bool = False):
        @contextlib.contextmanager
        def catcher():
            try:
                yield
            except exc_types as err:
                self.exception(msg, err)
                if reraise:
                    raise

        return catcher()

    @override
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} context={dict(self.context)!r}>"

    def __rich_repr__(self):
        yield "context", dict(self.context)

    __rich_repr__.angular = True  # pyright: ignore[reportFunctionMemberAccess]
