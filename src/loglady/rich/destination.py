# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""
A logging destination based on Rich's fancy-ass console output.
"""

from dataclasses import InitVar, dataclass, field
from typing import IO, override

from rich.console import Console
from rich.text import Text
from rich.theme import Theme

from loglady.processor import Processor
from loglady.record import Record

from . import formatters

DEFAULT_THEME = Theme(
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
    }
)


@dataclass(slots=True, kw_only=True)
class RichConsoleDestination(Processor):
    console: InitVar[Console | None] = None
    theme: InitVar[Theme | None] = None
    io: InitVar[IO[str] | None] = None

    formatter: formatters.RecordFormatter = field(default_factory=formatters.RecordFormatter)
    _console: Console = field(init=False)

    def __post_init__(self, console: Console | None, theme: Theme | None, io: IO[str] | None):
        theme = theme or DEFAULT_THEME

        if not console:
            console = Console(theme=theme, file=io)
        else:
            console.push_theme(theme)

        self._console = console

    @override
    def __call__(self, record: Record):
        try:
            self._console.print(self.formatter(record))
        except Exception as err:  # noqa: BLE001
            self._console.print(Text(f"Exception while formatting record: {err!r}", "log.level.error"))
