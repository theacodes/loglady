# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
Rich-based log renderer.
"""

from collections.abc import Mapping
from types import MappingProxyType

import rich
import rich.box
import rich.console
import rich.containers
import rich.highlighter
import rich.pretty
import rich.table
import rich.theme
import rich.traceback
from rich.text import Text

from loglady.types import Record

from . import formatters

_THEME = rich.theme.Theme(
    {
        "log.callsite": "cyan",
        "log.timestamp": "dim white",
        "log.thread": "default",
        "log.level": "default",
        "log.level.error": "bold red",
        "log.level.warning": "yellow",
        "log.level.success": "green",
        "log.level.info": "cyan",
        "log.level.debug": "violet",
        "log.level.notset": "gray70",
        "log.items.keys": "italic grey70",
        "log.items.values": "italic",
        "traceback.border": "red",
        "stacktrace.border": "cyan",
        "stacktrace.title": "cyan",
        "stacktrace.title.filename": "magenta",
        "stacktrace.title.lineno": "aquamarine1",
        "stacktrace.title.function": "chartreuse1",
    }
)


DEFAULT_FORMATTERS = MappingProxyType(
    dict(
        level=formatters.LevelFormatter(),
        message=formatters.MessageFormatter(),
        timestamp=formatters.NonrepeatedFormatter(formatters.TimestampFormatter(), fill=True),
        callsite=formatters.NonrepeatedFormatter(formatters.CallsiteFormatter()),
        items=formatters.RecordItemsFormatter(),
        thread=formatters.ThreadInfoFormatter(),
        exception=formatters.ExceptionFormatter(),
        stacktrace=formatters.StacktraceFormatter(),
    )
)


class LineFormatter:
    def __call__(self, formatted):
        table = rich.table.Table.grid(padding=(0, 1), expand=True)
        table.add_column(style="log.timestamp")
        table.add_column(style="log.level", width=1, overflow="crop")
        table.add_column(ratio=1, overflow="fold")
        table.add_column(style="log.callsite", justify="right")
        table.add_column(style="log.thread", width=1, overflow="ignore")

        msg_and_items = Text.assemble(formatted["message"], formatted["items"])
        msg_container = rich.containers.Renderables([msg_and_items])

        if exception := formatted.pop("exception", None):
            msg_container.append(exception)

        if stack := formatted.pop("stacktrace", None):
            msg_container.append(stack)

        table.add_row(
            formatted["timestamp"],
            formatted["level"],
            msg_container,
            formatted["callsite"],
            formatted["thread"],
        )

        return table


class RichRenderer:
    def __init__(
        self,
        *,
        formatters: Mapping[str, formatters.Formatter] = DEFAULT_FORMATTERS,
        line_formatter=None,
        theme=_THEME,
    ):
        super().__init__()
        self.formatters = formatters
        self.console = rich.console.Console(theme=theme)

        if line_formatter is None:
            line_formatter = LineFormatter()
        self.line_formatter = line_formatter

    def __call__(self, record: Record):
        c = self.console

        formatted = {}
        for name, fn in self.formatters.items():
            formatted[name] = fn(record)

        line = self.line_formatter(formatted)

        c.print(line)
