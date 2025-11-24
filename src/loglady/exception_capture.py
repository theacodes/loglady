# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for extracting and formatting exceptions and tracebacks."""

from __future__ import annotations

import contextlib
import reprlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from types import EllipsisType
from typing import Any, overload

from .stack_capture import CapturedFrame, CapturedStack


@dataclass(frozen=True, slots=True, kw_only=True)
class CapturedException:
    type: str
    module: str | None = None
    # NOTE: This can **not** be named str as it would cause Pydantic issues, see:
    # https://github.com/pydantic/pydantic/issues/12570
    string: str
    repr: str
    notes: Sequence[str] | None = None
    stack: Sequence[CapturedFrame] | None = None
    cause: CapturedException | None = None
    context: CapturedException | None = None
    exceptions: Sequence[CapturedException] | None = None
    suppress_context: bool = False

    @classmethod
    @overload
    def create(
        cls,
        exc: BaseException | CapturedException,
        *,
        stack_limit: EllipsisType | int = ...,
        capture_traceback: bool = True,
        capture_lines: bool = True,
        capture_locals: bool = False,
    ) -> CapturedException: ...

    @classmethod
    @overload
    def create(
        cls,
        exc: None,
        *,
        stack_limit: EllipsisType | int = ...,
        capture_traceback: bool = True,
        capture_lines: bool = True,
        capture_locals: bool = False,
    ) -> CapturedException | None: ...

    @classmethod
    def create(
        cls,
        exc: BaseException | CapturedException | None,
        *,
        stack_limit: EllipsisType | int = ...,
        capture_traceback: bool = True,
        capture_lines: bool = True,
        capture_locals: bool = False,
    ) -> CapturedException | None:
        match exc:
            case None:
                return capture_current_exception(
                    stack_limit=stack_limit,
                    capture_traceback=capture_traceback,
                    capture_lines=capture_lines,
                    capture_locals=capture_locals,
                )
            case _:
                return capture_exception(
                    exc,
                    stack_limit=stack_limit,
                    capture_traceback=capture_traceback,
                    capture_lines=capture_lines,
                    capture_locals=capture_locals,
                )


#
# Slightly lower-level methods for creating CapturedException types.
#


def capture_current_exception(
    *,
    stack_limit: EllipsisType | int = ...,
    capture_traceback: bool = True,
    capture_lines: bool = True,
    capture_locals: bool = False,
) -> CapturedException | None:
    _, exc, _ = sys.exc_info()

    if exc is None:
        return None

    return capture_exception(
        exc,
        stack_limit=stack_limit,
        capture_traceback=capture_traceback,
        capture_lines=capture_lines,
        capture_locals=capture_locals,
    )


def capture_exception(
    exc: BaseException | CapturedException,
    *,
    stack_limit: EllipsisType | int = ...,
    capture_traceback: bool = True,
    capture_lines: bool = True,
    capture_locals: bool = False,
    __depth: int = 0,
) -> CapturedException:
    """Convert an `Exception` or `traceback.TracebackException` to a limited dictionary representation with only
    primitive types.

    Holding onto `Exception` objects and their stack traces can be expensive (memory-wise) as well as cause odd
    behavior, so loglady eagerly captures them to plain objects. While this takes some time on the thread calling
    `log()`, it is much cheaper than holding onto the `Exception` object itself.
    """
    # TODO: Capture thread information.

    if isinstance(exc, CapturedException):
        return exc

    exc_type = type(exc)
    exc_type_name = exc_type.__qualname__
    exc_type_module = getattr(exc_type, "__module__", None)

    exc_str = _safe_str(exc)
    exc_repr = _safe_repr(exc)
    suppress_context = getattr(exc, "__suppress_context__", False)

    try:
        notes = getattr(exc, "__notes__", None)
    except Exception:  # noqa: BLE001
        notes = [f"<{exc_type_name}.__notes__() failed>"]

    # eagerly convert all notes to strings, just in case.
    if notes is not None:
        notes = tuple(_safe_str(note) for note in notes)

    if __depth > 1:
        return CapturedException(
            type=exc_type_name,
            module=exc_type_module,
            string=exc_str,
            repr=exc_repr,
            notes=notes,
            suppress_context=suppress_context,
        )

    if capture_traceback and (exc_traceback := _safe_getattr(exc, "__traceback__", None)) is not None:
        stack = CapturedStack.create(
            exc_traceback,
            limit=stack_limit,
            capture_lines=capture_lines,
            capture_locals=capture_locals,
        )
    else:
        stack = None

    if (cause_exc := _safe_getattr(exc, "__cause__", None)) is not None:
        cause = capture_exception(
            cause_exc,
            stack_limit=stack_limit,
            capture_lines=capture_lines,
            capture_locals=capture_locals,
            __depth=__depth + 1,
        )
    else:
        cause = None

    if not suppress_context and (context_exc := _safe_getattr(exc, "__context__", None)) is not None:
        context = capture_exception(
            context_exc,
            stack_limit=stack_limit,
            capture_lines=capture_lines,
            capture_locals=capture_locals,
            __depth=__depth + 1,
        )
    else:
        context = None

    if (grouped_excs := _safe_getattr(exc, "exceptions", None)) is not None:
        exceptions = tuple(
            capture_exception(
                exc,
                stack_limit=stack_limit,
                capture_lines=capture_lines,
                capture_locals=capture_locals,
                __depth=__depth + 1,
            )
            for exc in grouped_excs
        )
    else:
        exceptions = None

    return CapturedException(
        type=exc_type_name,
        module=exc_type_module,
        string=exc_str,
        repr=exc_repr,
        notes=notes,
        stack=stack,
        cause=cause,
        context=context,
        exceptions=exceptions,
    )


#
# Internal helpers
#


def _safe_str(value: Any) -> str:
    try:
        return str(value)
    except:  # noqa: E722
        return f"<str({type(value).__qualname__} @ {id(value)}) failed>"


def _safe_repr(value: Any) -> str:
    # reprlib will catch exceptions from `__repr__`, so we don't typically have to do that ourselves.
    return reprlib.repr(value)


def _safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    with contextlib.suppress(Exception):
        return getattr(obj, attr, default)
    return default
