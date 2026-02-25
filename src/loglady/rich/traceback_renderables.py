# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from rich import box
from rich.console import Console, ConsoleOptions, Group, RenderResult, group
from rich.constrain import Constrain
from rich.highlighter import ReprHighlighter
from rich.padding import Padding
from rich.panel import Panel
from rich.segment import Segment
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from loglady.exception_capture import CapturedException
from loglady.stack_capture import CapturedFrame


@dataclass(frozen=True, kw_only=True, slots=True)
class CapturedExceptionRenderable:
    exception: CapturedException
    depth: int = 0
    indent: int = 0

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        with console.use_theme(_traceback_theme):
            nl = Segment.line()
            indent_seg = Segment(
                ("│" + " " * self.indent * 2),
                style=console.get_style("traceback.indent"),
            )

            for line in console.render_lines(self._render(), pad=True):
                if self.indent:
                    yield indent_seg
                yield from line
                yield nl

    @group()
    def _render(self):
        nl = Segment.line()

        if self.depth == 0:
            yield Text("An exception occurred:", "traceback.title")
            yield nl

            if self.exception.cause:
                yield CapturedExceptionRenderable(
                    exception=self.exception.cause,
                    depth=self.depth + 1,
                    indent=self.indent,
                )
                yield nl
                yield Text("The previous exception was the direct cause of:", "traceback.cause")
                yield nl

            if self.exception.context:
                yield CapturedExceptionRenderable(
                    exception=self.exception.context,
                    depth=self.depth + 1,
                    indent=self.indent,
                )
                yield nl
                yield Text("While handling the above exception, another exception occurred:", "traceback.context")
                yield nl

        yield from self._traceback()
        yield from self._title()
        yield from self._notes()

        if self.exception.exceptions:
            for subexception in self.exception.exceptions:
                yield nl
                yield CapturedExceptionRenderable(exception=subexception, depth=self.depth + 1, indent=self.indent + 1)

        yield nl

    def _title(self):
        yield Text.assemble(
            *[
                (f"{self.exception.type}:", "traceback.exc_type"),
                (" ", ""),
                (self.exception.string, "traceback.exc_value"),
            ]
        )

    def _traceback(self):
        if self.exception.stack:
            yield CapturedStackRenderable(stack=self.exception.stack, title="Traceback")

    def _notes(self):
        for note in self.exception.notes or ():
            yield Text.from_markup(f"- {note}", style="traceback.note")


@dataclass(frozen=True, kw_only=True, slots=True)
class CapturedStackRenderable:
    stack: Iterable[CapturedFrame]
    title: str = "Stacktrace"
    width: int | None = None
    syntax_theme: str = "github-dark"

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        frames = reversed(list(self.stack))

        with console.use_theme(_traceback_theme):
            yield Text.assemble(
                (self.title, "stacktrace.title"),
                ": ",
                ("(most recent call last)", "stacktrace.aside"),
            )

            frames = Group(
                *(
                    Padding(
                        CapturedFrameRenderable(
                            frame=frame,
                            syntax_theme=self.syntax_theme,
                        ),
                        (1, 0, 0, 0),
                    )
                    for frame in frames
                    if not frame.is_hidden
                )
            )

            yield Constrain(frames, self.width)

        yield Segment.line()


@dataclass(slots=True, kw_only=True, frozen=True)
class CapturedFrameRenderable:
    frame: CapturedFrame
    syntax_theme: str = "github-dark"

    @property
    def is_hidden(self) -> bool:
        return self.frame.is_hidden

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        title = self._title(console)

        try:
            body = self._body()
            if body.renderables:
                body = Padding(body, (1, 0, 0, 0))

        except Exception as err:  # noqa: BLE001
            body = Text(f"\n{err}", "traceback.error")

        yield title
        yield body

    def _title(self, console: Console):
        has_source = not self.frame.filename.startswith("<")

        filename = self.frame.relative_filename
        filename_link = "file://{self.frame.filename}#{self.frame.lineno}" if has_source else None
        filename_style = console.get_style("stacktrace.filename").update_link(filename_link)
        lineno_style = console.get_style("stacktrace.lineno").update_link(filename_link)

        filename_part = Text.assemble(
            (filename, filename_style),
        )

        return Text.assemble(
            (" ↳ ", "stacktrace.decoration"),
            (f"{self.frame.name}()", "stacktrace.function"),
            (" in ", "stacktrace.text"),
            filename_part,
            (f":{self.frame.lineno}", lineno_style),
        )

    @group()
    def _body(self):
        line = self.frame.line
        lineno = self.frame.lineno

        has_source = not self.frame.filename.startswith("<")

        if has_source and line is not None and lineno is not None:
            yield Syntax(
                line.rstrip(),
                "python",
                # line_numbers=True,
                start_line=lineno,
                # highlight_lines={lineno},
                word_wrap=False,
                indent_guides=True,
                dedent=False,
                theme=self.syntax_theme,
                padding=(1, 3),
            )

        if self.frame.locals:
            yield Panel(
                self._locals(
                    hide_dunder=True,
                    hide_sunder=False,
                ),
                box=box.MINIMAL,
                style="background",
                padding=(0, 3),
            )

    def _locals(
        self,
        *,
        hide_dunder: bool = False,
        hide_sunder: bool = False,
    ):
        locals_ = self.frame.locals
        assert locals_ is not None

        table = Table.grid(padding=(0, 1), expand=True)
        table.add_column(justify="right")
        table.add_column(justify="left", ratio=1)

        for key, value in locals_.items():
            if hide_dunder and key.startswith("__"):
                continue
            if hide_sunder and key.startswith("_"):
                continue

            table.add_row(
                Text.assemble(
                    (key, "scope.key.special" if key.startswith("__") else "scope.key"),
                    (" =", "scope.equals"),
                ),
                _repr_highlighter(value),
            )

        return table


_repr_highlighter: Final[ReprHighlighter] = ReprHighlighter()


_traceback_theme: Final[Theme] = Theme(
    {
        "traceback.exc_type": "underline bold red",
        "traceback.exc_value": "bold bright_white",
        "traceback.title": "bold bright_red",
        "traceback.cause": "bold yellow",
        "traceback.context": "bold yellow",
        "traceback.note": "italic white",
        "traceback.indent": "gray19",
        "stacktrace.title": "bold white",
        "stacktrace.aside": "dim italic",
        "stacktrace.text": "white",
        "stacktrace.filename": "bright_magenta",
        "stacktrace.lineno": "bright_cyan",
        "stacktrace.function": "bright_green",
        "stacktrace.decoration": "dim",
    },
    inherit=True,
)
