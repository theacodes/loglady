# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Formatters for RichConsoleDestination
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import MappingProxyType, ModuleType

import rich
import rich.box
import rich.console
import rich.containers
import rich.highlighter
import rich.pretty
import rich.table
import rich.traceback
from rich.text import Text

from loglady.threading import thread_emoji
from loglady.types import Record

from ._stacktrace import Stacktrace

type Formatter = Callable[[Record], rich.console.RenderableType | None]


@dataclass
class ExceptionFormatter:
    width: int | None = None
    extra_lines: int = 1
    theme: str | None = "github-dark"
    word_wrap: bool = False
    show_locals: bool = True
    locals_max_length: int = 10
    locals_max_string: int = 80
    locals_hide_dunder: bool = True
    locals_hide_sunder: bool = False
    indent_guides: bool = True
    suppress: Iterable[str | ModuleType] = ()
    max_frames: int = 100

    def __call__(self, record):
        exc = record.pop("exception", None)

        if exc is None or exc == (None, None, None):
            return None

        return rich.traceback.Traceback.from_exception(
            *exc,
            width=self.width,
            extra_lines=self.extra_lines,
            theme=self.theme,
            word_wrap=self.word_wrap,
            show_locals=self.show_locals,
            locals_max_length=self.locals_max_length,
            locals_max_string=self.locals_max_string,
            locals_hide_dunder=self.locals_hide_dunder,
            locals_hide_sunder=self.locals_hide_sunder,
            indent_guides=self.indent_guides,
            suppress=self.suppress,
            max_frames=self.max_frames,
        )


class StacktraceFormatter:
    def __init__(self):
        super().__init__()

    def __call__(self, record):
        if (stack := record.pop("stacktrace", None)) is None:
            return None
        return Stacktrace(stack)


DEFAULT_LEVEL_TO_TEXT = MappingProxyType(
    dict(
        error=Text("█", style="log.level.error"),
        warning=Text("█", style="log.level.warning"),
        success=Text("█", style="log.level.success"),
        info=Text("█", style="log.level.info"),
        debug=Text("█", style="log.level.debug"),
        notset=Text("█", style="log.level.notset"),
    )
)


class LevelFormatter:
    def __init__(self, level_to_text=DEFAULT_LEVEL_TO_TEXT):
        super().__init__()
        self.level_to_text = level_to_text

    def __call__(self, record: Record):
        level = record.get("level", "notset")
        sash = self.level_to_text.get(level)
        return sash


class MessageFormatter:
    def __call__(self, record: Record):
        level = record.get("level", "notset")
        msg = record.pop("msg")
        prefix = record.pop("prefix", None)
        icon = record.pop("icon", "●" if prefix else "")
        if icon:
            icon = f" {icon} "

        formatted = Text.from_markup(text=f"{prefix if prefix else ""}{icon}{msg} ", style=f"log.level.{level}")

        return formatted


class TimestampFormatter:
    def __call__(self, record: Record):
        timestamp = record.pop("timestamp", None)

        if not timestamp:
            return None

        return timestamp.strftime(format="%H:%M")


class CallsiteFormatter:
    def __init__(self, *, include_module: bool = False, collapse_special: bool = True):
        super().__init__()
        self.include_module = include_module
        self.collapse_special = collapse_special

    def __call__(self, record: Record):
        func_name = record.pop("call_fn", None)

        if not func_name:
            return "."

        filename = record.pop("call_filename")
        module = record.pop("call_module")
        lineno = record.pop("call_lineno")

        if self.include_module:
            name = f"{module}:{func_name}()"
        else:
            name = f"{func_name}()"

        if self.collapse_special:
            name = name.replace("<module>", f"{module}()")
            name = name.replace(".<locals>", "()")
            name = name.replace(".__call__", "()")
            name = name.replace("()()", "()")

        return Text(name, style=f"link file://{filename}:{lineno}")


class NonrepeatedFormatter:
    def __init__(self, fn: Formatter, *, fillchar: str = "⋅", fill: bool = False):
        super().__init__()
        self._fn = fn
        self._fillchar = fillchar
        self._fill = fill
        self._last = None

    def __call__(self, record: Record):
        new = self._fn(record)

        if new == self._last:
            if self._fill:
                length = 1
                match new:
                    case str() | Text():
                        length = len(new)
                    case _:
                        length = 1
                new = Text(self._fillchar * length, style="log.repeated")
            else:
                new = Text(self._fillchar, style="log.repeated")
        else:
            self._last = new

        return new


DEFAULT_IGNORED_KEYS = frozenset(
    {
        "level",
        "msg",
        "prefix",
        "icon",
        "timestamp",
        "call_fn",
        "call_filename",
        "call_module",
        "call_lineno",
        "thread_id",
        "thread_name",
        "exception",
        "stacktrace",
    }
)


class RecordItemsFormatter:
    def __init__(self, ignored_keys=DEFAULT_IGNORED_KEYS):
        super().__init__()
        self.ignored_keys = ignored_keys
        self._hl = rich.highlighter.ReprHighlighter()

    def __call__(self, record: Record):
        return Text.assemble(*self._gen_items(record))

    def _gen_items(self, record: Record):
        for k, v in record.items():
            if k in self.ignored_keys:
                continue

            yield Text(f"{k}=", "log.items.keys")
            match v:
                case bool():
                    yield Text("true", "repr.bool_true") if v else Text("false", "repr.bool_false")
                case None:
                    yield Text("none", "repr.none")
                case _:
                    yield self._hl(repr(v))
            yield " "


class ThreadInfoFormatter:
    def __call__(self, record: Record):
        id_ = record.pop("thread_id", 0)
        _ = record.pop("thread_name", "")
        emoji = thread_emoji(id_)
        return Text(text=emoji)
