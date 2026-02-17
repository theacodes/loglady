# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Formatters for RichConsoleDestination
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, override

import rich
import rich.highlighter
from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderableType
from rich.containers import Renderables
from rich.table import Table
from rich.text import Text

from loglady.stack_capture import CapturedFrame
from loglady.types import Record, ReservedKeys

from .traceback_renderables import CapturedExceptionRenderable, CapturedStackRenderable


@dataclass(slots=True, kw_only=True)
class FormattedRecord(ConsoleRenderable):
    timestamp: Text | str
    level: Text | str
    message: Text | str
    callsite: Text | str
    thread: Text | str
    items: Text | str | None = None
    exception: RenderableType | None = None
    stack: RenderableType | None = None

    @override
    def __rich_console__(self, console: Console, options: ConsoleOptions):
        msg_and_items = Text.assemble(*filter(None, (self.message, self.items)))
        msg_container = Renderables([msg_and_items])

        table = self._make_table()
        table.add_row(
            self.timestamp,
            self.level,
            msg_container,
            self.callsite,
            self.thread,
        )
        yield table

        # We create a separate table for exception/stacktrace since we don't want the file name to eat into the
        # available space

        if not self.exception and not self.stack:
            return

        table = self._make_table()

        if self.exception:
            table.add_row(
                " " * len(self.timestamp),
                " " * len(self.level),
                self.exception,
                "",
                "",
            )

        if self.stack:
            table.add_row(
                " " * len(self.timestamp),
                " " * len(self.level),
                self.stack,
                "",
                "",
            )

        yield table

    def _make_table(self):
        table = Table.grid(padding=(0, 1), expand=True)
        table.add_column(style="log.timestamp")
        table.add_column(style="log.level", width=1, overflow="crop")
        table.add_column(ratio=1, overflow="fold")
        table.add_column(style="log.callsite", justify="right")
        table.add_column(style="log.thread", width=1, overflow="ignore", justify="right")
        return table


class TextPartFormatter(Protocol):
    def __call__(self, record: Record, original: Record) -> Text | str: ...


class ExtendedPartFormatter(Protocol):
    def __call__(self, record: Record, original: Record) -> RenderableType | None: ...


@dataclass(slots=True, kw_only=True)
class RecordFormatter:
    level: TextPartFormatter = field(default_factory=lambda: LevelFormatter())
    message: TextPartFormatter = field(default_factory=lambda: MessageFormatter())
    timestamp: TextPartFormatter = field(
        default_factory=lambda: NonrepeatedFormatter(formatter=TimestampFormatter(), fill=True)
    )
    callsite: TextPartFormatter = field(default_factory=lambda: NonrepeatedFormatter(formatter=CallInfoFormatter()))
    thread: TextPartFormatter = field(
        default_factory=lambda: NonrepeatedFormatter(formatter=ThreadInfoFormatter(), fillchar="⋅", fill=True)
    )
    exception: ExtendedPartFormatter = field(default_factory=lambda: CapturedExceptionFormatter())
    stack: ExtendedPartFormatter = field(default_factory=lambda: CapturedStackFormatter())
    items: TextPartFormatter = field(default_factory=lambda: RecordItemsFormatter())

    def __call__(self, record: Record) -> FormattedRecord:
        original = dict(record)
        return FormattedRecord(
            timestamp=self.timestamp(record, original),
            level=self.level(record, original),
            callsite=self.callsite(record, original),
            thread=self.thread(record, original),
            exception=self.exception(record, original),
            stack=self.stack(record, original),
            message=self.message(record, original),
            items=self.items(record, original),
        )


@dataclass(slots=True)
class CapturedExceptionFormatter(ExtendedPartFormatter):
    @override
    def __call__(self, record: Record, original: Record):
        if (exc := record.pop(ReservedKeys.captured_exception, None)) is None:
            return None
        return CapturedExceptionRenderable(exception=exc)


@dataclass(slots=True)
class CapturedStackFormatter(ExtendedPartFormatter):
    @override
    def __call__(self, record: Record, original: Record):
        if (stack := record.pop(ReservedKeys.captured_stack, None)) is None:
            return None
        return CapturedStackRenderable(stack=stack)


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
DEFAULT_NOTSET_TEXT = Text("?", style="log.level.notset")


@dataclass(slots=True)
class LevelFormatter(TextPartFormatter):
    level_to_text: Mapping[str, Text] = DEFAULT_LEVEL_TO_TEXT

    @override
    def __call__(self, record: Record, original: Record):
        level = record.pop(ReservedKeys.level, "notset")
        sash = self.level_to_text.get(level, DEFAULT_NOTSET_TEXT)
        return sash


@dataclass(slots=True)
class MessageFormatter(TextPartFormatter):
    @override
    def __call__(self, record: Record, original: Record):
        level = original.get(ReservedKeys.level, "notset")
        msg = record.pop(ReservedKeys.msg)
        prefix = record.pop(ReservedKeys.prefix, None)
        icon = record.pop(ReservedKeys.icon, "●" if prefix else "")
        if icon:
            icon = f" {icon} "

        formatted = Text.from_markup(text=f"{prefix if prefix else ''}{icon}{msg} ", style=f"log.level.{level}")

        return formatted


@dataclass(slots=True)
class TimestampFormatter(TextPartFormatter):
    @override
    def __call__(self, record: Record, original: Record):
        timestamp = record.pop(ReservedKeys.timestamp, None)

        if not timestamp:
            return ""

        return timestamp.strftime(format="%H:%M")


@dataclass(slots=True)
class CallInfoFormatter(TextPartFormatter):
    include_module: bool = False
    collapse_special: bool = True

    @override
    def __call__(self, record: Record, original: Record):
        info: CapturedFrame | None = record.pop(ReservedKeys.captured_call_info, None)

        if info is None:
            return "."

        if self.include_module:
            name = f"{info.module_name}:{info.qualname}()"
        else:
            name = f"{info.qualname}()"

        if self.collapse_special:
            name = name.replace("<module>", f"{info.module_name}()")
            name = name.replace(".<locals>", "()")
            name = name.replace(".__call__", "()")
            name = name.replace("()()", "()")

        return Text(name, style=f"link file://{info.filename}:{info.lineno}")


@dataclass(slots=True, kw_only=True)
class NonrepeatedFormatter(TextPartFormatter):
    formatter: TextPartFormatter
    fillchar: str = "⋅"
    fill: bool = False

    _last: Any = field(init=False, default=None)

    @override
    def __call__(self, record: Record, original: Record):
        new = self.formatter(record, original)

        if new == self._last:
            if self.fill:
                length = 1
                match new:
                    case str() | Text():
                        length = len(new)
                    case _:
                        length = 1
                new = Text(self.fillchar * length, style="log.repeated")
            else:
                new = Text(self.fillchar, style="log.repeated")
        else:
            self._last = new

        return new


@dataclass(slots=True)
class RecordItemsFormatter(TextPartFormatter):
    _hl: rich.highlighter.ReprHighlighter = field(init=False, default_factory=rich.highlighter.ReprHighlighter)

    @override
    def __call__(self, record: Record, original: Record):
        return Text.assemble(*self._gen_items(record))

    def _gen_items(self, record: Record):
        for k, v in record.items():
            yield Text(f"{k}=", "log.items.keys")
            match v:
                case bool():
                    yield Text("true", "repr.bool_true") if v else Text("false", "repr.bool_false")
                case None:
                    yield Text("none", "repr.none")
                case _:
                    yield self._hl(repr(v))
            yield " "


@dataclass(slots=True)
class ThreadInfoFormatter(TextPartFormatter):
    @override
    def __call__(self, record: Record, original: Record):
        if (info := record.pop(ReservedKeys.captured_thread_info, None)) is None:
            return ""

        return Text(text=info.emoji)
