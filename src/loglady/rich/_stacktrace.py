# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Rich-compatible stacktrace printer.

Rich doesn't have a way to nicely print stacktraces without an Exception involved,
so this module allows for log.trace() to print out the stacktrace.

It's a lot of code. It's mostly because Thea can't leave well enough alone.
"""

import linecache
import os
from collections.abc import Iterator
from types import FrameType
from typing import Any

import pygments.token
from rich import box
from rich.console import Console, ConsoleOptions, RenderResult, group
from rich.constrain import Constrain
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.pretty import Pretty
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from loglady._tracebackhide import check_for_tracebackhide


class Stacktrace:
    def __init__(self, stack, *, width: int | None = None, extra_lines: int = 3, syntax_theme: str = "github-dark"):
        super().__init__()
        self.stack = stack
        self.width = width
        self.extra_lines = extra_lines
        self.syntax_theme = syntax_theme

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        frames = reversed(list(_iter_stack(self.stack)))

        traceback_theme = _make_theme()

        with console.use_theme(traceback_theme):
            frame_renderable = Panel(
                self._render_frames(frames),
                title="[stacktrace.title]Stacktrace",
                subtitle="[dim](most recent call last)",
                border_style="stacktrace.border",
                expand=True,
                padding=(0, 1),
            )

            stack_renderable = Constrain(frame_renderable, self.width)

            yield stack_renderable

    @group()
    def _render_frames(self, frames: Iterator["_Stackframe"]):
        for n, frame in enumerate(frames):
            yield frame.render(n, extra_lines=self.extra_lines, syntax_theme=self.syntax_theme)


class _Stackframe:
    def __init__(self, frame: FrameType):
        super().__init__()
        self.filename = frame.f_code.co_filename
        self.lineno = frame.f_lineno
        self.fn = frame.f_code.co_name
        self.is_from_file = not self.filename.startswith("<")
        self.is_module = self.fn.startswith("<")
        if self.is_from_file and not self.is_module:
            self.locals = frame.f_locals
        else:
            self.locals = None

        self.is_hidden = (not self.is_from_file) or check_for_tracebackhide(frame)

    @property
    def code(self):
        return "".join(linecache.getlines(self.filename))

    @property
    def relpath(self):
        relpath = os.path.relpath(self.filename)

        if relpath != self.filename:
            relpath = f"./{relpath}"

        return relpath

    @group()
    def render(self, n: int, *, extra_lines: int, syntax_theme: str):
        title = self.title(n=n)

        try:
            body = self.body(extra_lines=extra_lines, syntax_theme=syntax_theme)
        except Exception as err:  # noqa: BLE001
            body = Text(f"\n{err}", "traceback.error")

        if n > 0 and self.is_from_file:
            yield ""

        yield title
        yield body

    def title(self, n: int):
        # Path and function name
        path = self.relpath if self.is_from_file else self.filename
        highlighter = _PathHighlighter()

        return Text.assemble(
            (f"#{n}:", "stacktrace.title"),
            highlighter(Text(path, style="stacktrace.title.filename")),
            (":", "stacktrace.title"),
            (str(self.lineno), "stacktrace.title.lineno"),
            (" @ ", "stacktrace.title"),
            (self.fn, "stacktrace.title.function"),
        )

    @group()
    def body(self, *, extra_lines: int, syntax_theme: str):
        code = self.code
        if not code:
            return

        yield Syntax(
            code,
            "python",
            line_numbers=True,
            line_range=(
                self.lineno - extra_lines,
                self.lineno + extra_lines,
            ),
            highlight_lines={self.lineno},
            word_wrap=False,
            indent_guides=True,
            dedent=False,
            theme=syntax_theme,
        )

        if self.locals:
            yield Panel(
                _render_locals(
                    self.locals,
                    hide_dunder=True,
                    hide_sunder=False,
                ),
                box=box.MINIMAL,
                style="background",
                padding=(0, 0),
            )


class _PathHighlighter(RegexHighlighter):
    def __init__(self):
        super().__init__()
        self.highlights = [r"(?P<inherit>.*/)(?P<bold>.+)"]


def _iter_stack(stack: FrameType):
    frame = stack
    while frame:
        sf = _Stackframe(frame)
        if not sf.is_hidden:
            yield sf
        frame = frame.f_back


def _render_locals(frame_locals: dict[str, Any], *, hide_dunder: bool, hide_sunder: bool):
    """Render a frame's local variables."""
    table = Table.grid(padding=(0, 1), expand=True)
    table.add_column(justify="right")
    table.add_column(justify="left", ratio=1)

    for key, value in frame_locals.items():
        if hide_dunder and key.startswith("__"):
            continue
        if hide_sunder and key.startswith("_"):
            continue

        table.add_row(
            Text.assemble(
                (key, "scope.key.special" if key.startswith("__") else "scope.key"),
                (" =", "scope.equals"),
            ),
            Pretty(value),
        )

    return table


def _make_theme(name: str = "dracula") -> Theme:
    """Make a Rich theme from a pygments theme. Based on code in rich.traceback"""
    syntax_theme = Syntax.get_theme(name)
    token_style = syntax_theme.get_style_for_token
    tks = pygments.token
    traceback_theme = Theme(
        {
            "background": syntax_theme.get_background_style(),
            "pretty": token_style(tks.Text),
            "pygments.text": token_style(tks.Token),
            "pygments.string": token_style(tks.String),
            "pygments.function": token_style(tks.Name.Function),
            "pygments.number": token_style(tks.Number),
            "repr.indent": token_style(tks.Comment) + Style(dim=True),
            "repr.str": token_style(tks.String),
            "repr.brace": token_style(tks.Text) + Style(bold=True),
            "repr.number": token_style(tks.Number),
            "repr.bool_true": token_style(tks.Keyword.Constant),
            "repr.bool_false": token_style(tks.Keyword.Constant),
            "repr.none": token_style(tks.Keyword.Constant),
            "scope.border": token_style(tks.String.Delimiter),
            "scope.equals": token_style(tks.Operator),
            "scope.key": token_style(tks.Name),
            "scope.key.special": token_style(tks.Name.Constant) + Style(dim=True),
        },
        inherit=False,
    )
    return traceback_theme
