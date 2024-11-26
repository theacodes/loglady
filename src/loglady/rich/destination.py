# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
A logging destination based on Rich's fancy-ass console output.
"""

from collections.abc import Mapping
from typing import IO, override
from warnings import warn

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

from loglady.destination import Destination
from loglady.types import Record

from . import formatters

DEFAULT_THEME = rich.theme.Theme(
    {
        "log.callsite": "cyan",
        "log.timestamp": "grey62",
        "log.thread": "default",
        "log.level": "default",
        "log.repeated": "grey23",
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


def make_default_formatters():
    return dict(
        level=formatters.LevelFormatter(),
        message=formatters.MessageFormatter(),
        timestamp=formatters.NonrepeatedFormatter(formatters.TimestampFormatter(), fill=True),
        callsite=formatters.NonrepeatedFormatter(formatters.CallsiteFormatter()),
        items=formatters.RecordItemsFormatter(),
        thread=formatters.NonrepeatedFormatter(formatters.ThreadInfoFormatter(), fillchar="⋅", fill=True),
        exception=formatters.ExceptionFormatter(),
        stacktrace=formatters.StacktraceFormatter(),
    )


class LineFormatter:
    def __call__(self, formatted):
        msg_and_items = Text.assemble(formatted["message"], formatted["items"])
        msg_container = rich.containers.Renderables([msg_and_items])

        table = self._make_table()
        table.add_row(
            formatted["timestamp"],
            formatted["level"],
            msg_container,
            formatted["callsite"],
            formatted["thread"],
        )

        yield table

        if exception := formatted.pop("exception", None):
            table = self._make_table()
            table.add_row(
                " " * len(formatted["timestamp"]),
                " " * len(formatted["level"]),
                exception,
                "",
                "",
            )
            yield table

        if stack := formatted.pop("stacktrace", None):
            table = self._make_table()
            table.add_row(
                " " * len(formatted["timestamp"]),
                " " * len(formatted["level"]),
                stack,
                "",
                "",
            )
            yield table

    def _make_table(self):
        table = rich.table.Table.grid(padding=(0, 1), expand=True)
        table.add_column(style="log.timestamp")
        table.add_column(style="log.level", width=1, overflow="crop")
        table.add_column(ratio=1, overflow="fold")
        table.add_column(style="log.callsite", justify="right")
        table.add_column(style="log.thread", width=1, overflow="ignore", justify="right")
        return table


class RichConsoleDestination(Destination):
    def __init__(
        self,
        *,
        formatters: Mapping[str, formatters.Formatter] | None = None,
        line_formatter=None,
        theme=DEFAULT_THEME,
        io: IO[str] | None = None,
        console: rich.console.Console | None = None,
    ):
        super().__init__()

        if formatters is None:
            formatters = make_default_formatters()

        self.formatters = formatters

        if not console:
            console = rich.console.Console(theme=theme, file=io)
        else:
            console.push_theme(theme)

        self.console = console

        if line_formatter is None:
            line_formatter = LineFormatter()
        self.line_formatter = line_formatter

    @override
    def __call__(self, record: Record):
        c = self.console

        formatted = {}
        for name, fn in self.formatters.items():
            try:
                formatted[name] = fn(record)
            except Exception as err:  # noqa: BLE001
                warn(f"exception while invoking formatter {fn!r}: {err!r}", stacklevel=1)

        for line in self.line_formatter(formatted):
            c.print(line)
