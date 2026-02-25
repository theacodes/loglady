# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for introspecting and capturing stack traces.

This is similar to the utilities found in `inspect.stack()` and `traceback`, but optimized for Loglady's use cases-
specifically, capturing a minimum about of info about stack frames in a way that's easy to copy, transfer, and
serialize.
"""

from __future__ import annotations

import contextlib
import importlib
import itertools
import linecache
import os
import pathlib
import reprlib
import sys
import sysconfig
from collections.abc import Callable, Generator, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import EllipsisType, FrameType, ModuleType, TracebackType
from typing import Any, Final, cast, overload, override

#
# High-level interface
#


@dataclass(frozen=True, slots=True, kw_only=True)
class CapturedFrame:
    filename: str
    lineno: int | None
    name: str
    qualname: str
    module_name: str = "<unknown>"
    line: str | None = field(default=None, compare=False, hash=False)
    locals: dict[str, str] | None = field(default=None, compare=False, hash=False)
    is_hidden: bool = False

    @property
    def relative_filename(self):
        return _source_relpath(self.filename)

    def resolve_module(self) -> ModuleType | None:
        if self.module_name.startswith("<"):
            return None
        return importlib.import_module(self.module_name)

    @classmethod
    def create(
        cls,
        frame: FrameType | TracebackType,
        *,
        capture_line: bool = True,
        capture_locals: bool = False,
    ) -> CapturedFrame:
        return capture_frame(frame, capture_line=capture_line, capture_locals=capture_locals)

    @classmethod
    def create_from_caller(
        cls,
        *,
        exclude: Iterable[FrameSourceLike] = (),
        include_stdlib: bool = False,
        capture_line: bool = True,
        capture_locals: bool = False,
    ) -> CapturedFrame | None:
        caller = infer_caller(exclude=exclude, include_stdlib=include_stdlib, depth=1)
        if caller is None:
            return None
        return capture_frame(caller, capture_line=capture_line, capture_locals=capture_locals)


@dataclass(frozen=True, slots=True, kw_only=True)
class CapturedStack(Sequence[CapturedFrame]):
    frames: Sequence[CapturedFrame]

    @classmethod
    def create(
        cls,
        start: FrameType | TracebackType,
        *,
        limit: int | EllipsisType = ...,
        capture_lines: bool = True,
        capture_locals: bool = False,
        keep_hidden: bool = False,
        reverse: bool = False,
    ) -> CapturedStack:
        return capture_stack(
            start,
            limit=limit,
            capture_lines=capture_lines,
            capture_locals=capture_locals,
            keep_hidden=keep_hidden,
            reverse=reverse,
        )

    @classmethod
    def create_from_caller(
        cls,
        *,
        exclude: Iterable[FrameSourceLike] = (),
        include_stdlib: bool = True,
        limit: int | EllipsisType = ...,
        capture_lines: bool = True,
        capture_locals: bool = False,
        keep_hidden: bool = False,
    ):
        start = infer_caller(exclude=exclude, include_stdlib=include_stdlib)
        if start is None:
            return None
        return capture_stack(
            start,
            limit=limit,
            capture_lines=capture_lines,
            capture_locals=capture_locals,
            keep_hidden=keep_hidden,
        )

    def visible_frames(self) -> Generator[CapturedFrame]:
        yield from (frame for frame in self.frames if not frame.is_hidden)

    def hidden_frames(self) -> Generator[CapturedFrame]:
        yield from (frame for frame in self.frames if frame.is_hidden)

    @overload
    def __getitem__(self, index: int) -> CapturedFrame: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[CapturedFrame]: ...

    @override
    def __getitem__(self, index: int | slice) -> CapturedFrame | Sequence[CapturedFrame]:
        return self.frames[index]

    @override
    def index(self, value: CapturedFrame, *args, **kwargs) -> int:
        return self.frames.index(value, *args, **kwargs)

    @override
    def count(self, value: CapturedFrame) -> int:
        return self.frames.count(value)

    @override
    def __contains__(self, value: object) -> bool:
        return self.frames.__contains__(value)

    @override
    def __iter__(self) -> Iterator[CapturedFrame]:
        return self.frames.__iter__()

    @override
    def __reversed__(self) -> Iterator[CapturedFrame]:
        return self.frames.__reversed__()

    @override
    def __len__(self) -> int:
        return self.frames.__len__()


#
# Slightly lower-level functions for constructing `CapturedStack` and `CapturedFrame` objects.
#


def capture_stack(
    start: FrameType | TracebackType | None = None,
    *,
    limit: int | EllipsisType = ...,
    capture_lines: bool = True,
    capture_locals: bool = False,
    keep_hidden: bool = False,
    reverse: bool = False,
) -> CapturedStack:
    def predicate(frame: FrameType) -> bool:
        return not is_frame_hidden(frame)

    stack_ = stack(
        start,
        predicate=predicate,
        limit=limit,
        include_elided=True,
        depth=1,
    )
    frames = []

    for frame_ in stack_:
        match frame_:
            case FrameType():
                frames.append(CapturedFrame.create(frame_, capture_line=capture_lines, capture_locals=capture_locals))
            case ElidedFrame() if keep_hidden:
                frames.append(CapturedFrame.create(frame_.frame, capture_line=False, capture_locals=False))
            case _:
                pass

    if reverse:
        frames.reverse()

    return CapturedStack(frames=tuple(frames))


def capture_frame(
    frame: FrameType | TracebackType,
    *,
    capture_line: bool = True,
    capture_locals: bool = False,
) -> CapturedFrame:
    if isinstance(frame, TracebackType):
        frame = frame.tb_frame

    filename = frame.f_code.co_filename
    lineno = frame.f_lineno

    line = None
    if capture_line:
        with contextlib.suppress(Exception):
            line = linecache.getline(filename, lineno)

    locals_ = None
    if capture_locals:
        locals_ = {k: _safe_repr(v) for k, v in frame.f_locals.items()}

    is_hidden = is_frame_hidden(frame)

    module_name = "<unknown>"
    # f_globals should be a dict but can technically be anything, so be extra careful here.
    with contextlib.suppress(Exception):
        module_name: str = frame.f_globals.get("__name__", "<unknown>")

    return CapturedFrame(
        filename=filename,
        lineno=lineno,
        name=frame.f_code.co_name,
        qualname=frame.f_code.co_qualname,
        module_name=module_name,
        line=line,
        locals=locals_,
        is_hidden=is_hidden,
    )


#
# Lower-level stack introspection, returning bare FrameTypes.
#

type FrameSourceLike = ModuleType | Path | str


def infer_caller(
    *, exclude: Iterable[FrameSourceLike] = (), include_stdlib: bool = False, depth: int = 0
) -> FrameType | None:
    """Determines the first caller that is not defined in the excluded list.

    The excluded list can be a set of modules, packages, or files. Modules in the standard library are excluded by
    default unless `include_stdlib` is set to `True`.

    If no caller is found, returns `None`.

    Adapted from `importlib.resources`.

    Refs:
    - https://github.com/python/cpython/blob/03017a8cc2242d881a3042b1eb9084c9bae9f85d/Lib/importlib/resources/_common.py#L90
    """

    is_in_exclude = create_is_frame_from(__file__, *exclude)
    predicates = (is_in_exclude, is_frame_hidden, is_frame_from_loglady)

    if not include_stdlib:
        predicates = (is_frame_from_stdlib, *predicates)

    def predicate(frame: FrameType):
        return not any(predicate(frame) for predicate in predicates)

    for frame in stack(predicate=predicate, depth=depth + 1):
        return frame

    return None


type FramePredicate = Callable[[FrameType], bool]


@overload
def stack(
    start: FrameType | TracebackType | None = None,
    *,
    predicate: FramePredicate | None = None,
    limit: int | EllipsisType = ...,
    depth: int = 0,
) -> Generator[FrameType]: ...


@overload
def stack(
    start: FrameType | TracebackType | None = None,
    *,
    predicate: FramePredicate,
    limit: int | EllipsisType = ...,
    depth: int = 0,
    include_elided: bool = True,
) -> Generator[FrameType | ElidedFrame]: ...


def stack(
    start: FrameType | TracebackType | None = None,
    *,
    predicate: FramePredicate | None = None,
    limit: int | EllipsisType = ...,
    depth: int = 0,
    include_elided: bool = False,
) -> Generator[FrameType] | Generator[FrameType | ElidedFrame]:
    """Returns yields frames from the caller's current stack, optionally filtered by a predicate and with elision.

    Unlike `traceback.walk_stack()`, this allow control filtering with a predicate and allows for controlled elision of
    frames.

    - `predicate` should return `True` for frames that should be kept. If `predicate` is not specified, all frames are
       yielded.
    - `included_elided` causes elided frames to be yield as `ElidedFrame` items instead of silently dropped.

    Unlike `inspect.stack()`, this function does not return a list of `inspect.FrameInfo`, since constructing those can
    be expensive as it requires reading the source file for each frame in the stack.
    """
    if start is None:
        start = get_frame(depth + 2)

    if limit is ...:
        limit = cast(int, getattr(sys, "tracebacklimit", 50))

    stack_ = itertools.islice(_stack_gen(start), limit)

    if predicate is None:
        yield from stack_
        return

    if include_elided is False:
        yield from filter(predicate, stack_)
        return

    for item in stack_:
        if predicate(item):
            yield item
        else:
            yield ElidedFrame(item)
    return


@dataclass(frozen=True, slots=True)
class ElidedFrame:
    """A frame that has been elided from the stack trace."""

    frame: FrameType


#
# Low-level helpers
#


def get_frame(depth: int = 1) -> FrameType:
    """Alias to `sys._getframe(depth)`.

    NOTE: Using `sys._getframe()` is significantly faster than using `inspect.stack()`, as the latter ends up getting
     source file data for every frame in the stack. Despite the `_`, `_getframe()` is documented and safe to use in
     CPython since `2.1`.

    Refs:
    -
    """
    return sys._getframe(depth + 1)  # pyright: ignore[reportPrivateUsage]


def is_frame_hidden(frame: FrameType) -> bool:
    """Checks if a stack frame is "hidden".

    Hidden frames satisfy one of the following:

    - Has `__tracebackhide__` defined, the value does not matter.
    - Has `__traceback_hide__` defined, the value does not matter.

    This is adapted from pytest's `TracebackEntry.ishidden`.
    """
    # Note that f_locals and f_globals are normally dictionaries, but with
    # exec() and eval() they can be set to just about anything, so we swallow
    # all exceptions while trying this nonsense.
    with contextlib.suppress(Exception):
        for namespace in (frame.f_locals, frame.f_globals):
            if "__tracebackhide__" in namespace:
                return True
            if "__traceback_hide__" in namespace:
                return True

    return False


def create_is_frame_from(*sources: FrameSourceLike) -> FramePredicate:
    """Create a predicate that matches frames from the given modules, packages, or files."""

    sources = tuple(_validate_source(source) for source in sources)
    source_files = tuple(item for item in sources if item.endswith((".py", ".pyc", ".pyo")))
    source_paths = tuple(item for item in sources if not item.endswith((".py", ".pyc", ".pyo")))

    def predicate(frame: FrameType) -> bool:
        filename = frame.f_code.co_filename

        if filename in source_files:
            return True
        if filename.startswith(source_paths):  # noqa: SIM103
            return True

        return False

    return predicate


def is_frame_from_stdlib(frame: FrameType) -> bool:
    """A predicate that matches frames from the Python standard library."""
    filename = frame.f_code.co_filename
    return filename.startswith(_STDLIB_PATH)


_STDLIB_PATH: Final[str] = sysconfig.get_path("stdlib")


def is_frame_from_site_packages(frame: FrameType) -> bool:
    """A predicate that matches frames from the Python site-packages directory."""
    filename = frame.f_code.co_filename
    return filename.startswith(_SITE_PACKAGES_PATH)


_SITE_PACKAGES_PATH: Final[str] = sysconfig.get_path("platlib")


def is_frame_from_loglady(frame: FrameType):
    filename = frame.f_code.co_filename
    return filename.startswith(_LOGLADY_PATH)


_LOGLADY_PATH: Final[str] = str(pathlib.Path(__file__).parent) + os.sep

#
# Internal helpers
#


def _safe_repr(value: Any) -> str:
    # reprlib will catch exceptions from `__repr__`, so we don't typically have to do that ourselves.
    return reprlib.repr(value)


def _stack_gen(start: FrameType | TracebackType | None) -> Generator[FrameType]:
    match start:
        case None:
            return
        case FrameType():
            yield from _stack_from_frame(start)
        case TracebackType():
            yield from _stack_from_traceback(start)


def _stack_from_frame(start: FrameType | None) -> Generator[FrameType]:
    current = start
    while current:
        yield current
        current = current.f_back


def _stack_from_traceback(start: TracebackType | None) -> Generator[FrameType]:
    current = start
    while current:
        yield current.tb_frame
        current = current.tb_next


def _validate_source(source: ModuleType | Path | str) -> str:
    match source:
        case str() if "/" in source or source.endswith((".py", ".pyc", ".pyo")):
            # almost certainly a file path.
            return source
        case str() if source in sys.modules:
            # This is definitely a module name.
            return _validate_source(sys.modules[source])
        case str():
            # Not sure what this is, so just pass it through as is.
            return source
        case Path():
            return str(source)
        case ModuleType() if source.__file__ is not None:
            if source.__file__.endswith("__init__.py"):
                # If the module is a package, we want the parent directory.
                return str(Path(source.__file__).parent)
            return source.__file__
        case _:
            msg = f"source must be a file path, module name, Path, or ModuleType with a __file__ attribute, got {source!r}"
            raise ValueError(msg)


def _source_relpath(filename: str) -> str:
    if filename.startswith(_STDLIB_PATH):
        return f"<stdlib>{filename[len(_STDLIB_PATH) :]}"

    if filename.startswith(_SITE_PACKAGES_PATH):
        return f"<site-packages>{filename[len(_SITE_PACKAGES_PATH) :]}"

    relpath = os.path.relpath(filename)

    if relpath != filename:
        relpath = f"./{relpath}"

    return relpath
