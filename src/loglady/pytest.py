# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

import contextlib
from collections import UserString
from collections.abc import Generator
from io import StringIO
from typing import cast

import pytest
import rich

from . import config, manager_stack
from .destination import CaptureDestination
from .rich.destination import RichConsoleDestination
from .transport import SyncTransport
from .types import Record


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    _ = config.pluginmanager.register(LogladyPlugin(config), "loglady-plugin")


def pytest_addoption(parser):
    group = parser.getgroup("loglady", "loglady capturing options.")
    group.addoption(
        "--loglady-disable-deferred-formatting",
        action="store_true",
        default=False,
        help="Disable deferred formatting of captured logs. Deferred formatting prevent unnecessarily formatting logs that are not ever seen, which can slow down tests.",
    )


class LogladyPlugin:
    """
    Plugin for pytest that gathers global logs and associates them with tests.

    This is intended to function like pytest's build-in capsys and caplog features.

    Refs:
    - https://github.com/pytest-dev/pytest/blob/72c682ff9773ad2690711105a100423ebf7c7c15/src/_pytest/capture.py#L709-L710
    """

    def __init__(self, config: pytest.Config) -> None:
        super().__init__()
        self.config = config
        self._global_captured = None
        self._fixture_captured = None
        self._manager = None
        self._has_fixture = False

    @property
    def use_color(self) -> bool:
        return self.config.option.color != "no"

    @property
    def disable_deferred_formatting(self) -> bool:
        return self.config.option.loglady_disable_deferred_formatting

    def start_global_capturing(self):
        self._global_captured = CaptureDestination()
        self._manager = config.configure(
            transport=SyncTransport(),
            middleware=config.DEFAULT_MIDDLEWARE,
            destinations=[self._global_captured],
            install_hook=False,
            once=False,
        )

    def stop_global_capturing(self):
        if self._manager is None:
            return

        self._manager.flush()
        self._manager.stop()
        _ = manager_stack.pop()

    def enable_fixture(self):
        self._fixture_captured = CaptureDestination()
        return self._fixture_captured

    def disable_fixture(self):
        self._fixture_captured = None

    def activate_fixture(self):
        if self._fixture_captured is None:
            return

        assert self._manager is not None
        self._manager.destinations = [self._fixture_captured]

    def deactivate_fixture(self):
        assert self._manager is not None
        assert self._global_captured is not None
        self._manager.destinations = [self._global_captured]

    def grab_captured_output(self) -> str:
        assert self._global_captured is not None
        capture = _DeferredCapturedOutput.create(self._global_captured)

        if self.disable_deferred_formatting:
            return capture.render(use_color=self.use_color)

        return cast(str, capture)

    @contextlib.contextmanager
    def item_capture(self, when: str, item: pytest.Item) -> Generator[None]:
        self.start_global_capturing()
        self.activate_fixture()
        try:
            yield
        finally:
            self.deactivate_fixture()
            self.stop_global_capturing()
            item.add_report_section(when, "loglady", self.grab_captured_output())

    # Hooks

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_setup(self, item: pytest.Item) -> Generator[None]:
        with self.item_capture("setup", item):
            return (yield)

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_call(self, item: pytest.Item) -> Generator[None]:
        with self.item_capture("call", item):
            return (yield)

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_teardown(self, item: pytest.Item) -> Generator[None]:
        with self.item_capture("teardown", item):
            return (yield)

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus: pytest.ExitCode, config: pytest.Config):
        for category, reports in terminalreporter.stats.items():
            for report in reports:
                for n, (section, content) in enumerate(report.sections):
                    if isinstance(content, _DeferredCapturedOutput):
                        if category in ("failed", "error", ""):  # NOTE: "" is used for teardown
                            report.sections[n] = (section, content.render(use_color=self.use_color))
                        else:
                            report.sections[n] = (section, content.data + f"({category=}, {section=})")

        return (yield)

    @pytest.hookimpl(tryfirst=True)
    def pytest_keyboard_interrupt(self) -> None:
        self.stop_global_capturing()

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(self) -> None:
        self.stop_global_capturing()


class _DeferredCapturedOutput(UserString):
    def __init__(self, value: str):
        super().__init__(value)
        self.captured: CaptureDestination | None = None
        self.rendered: str | None = None

    @classmethod
    def create(cls, captured: CaptureDestination) -> _DeferredCapturedOutput:
        inst = cls(
            f"Captured {len(captured.records)} records. Loglady did not format these records because it thought no "
            f"one would ever try to look at them, pass --loglady-disable-deferred-formatting to force it to format "
            f"them anyway."
        )
        inst.captured = captured
        return inst

    def render(self, *, use_color: bool = True) -> str:
        if self.rendered is not None:
            return self.rendered

        if self.captured is None:
            return self.data

        io = StringIO()
        console = rich.console.Console(
            file=io,
            force_terminal=use_color,
            force_interactive=False,
            force_jupyter=False,
        )
        console_dest = RichConsoleDestination(console=console)

        self.captured.playback(console_dest)

        self.captured = None
        self.rendered = io.getvalue()
        return self.rendered


@pytest.fixture
def loglady_capture(request: pytest.FixtureRequest) -> Generator[list[Record], None, None]:
    """A fixture that captures global loglady logs and yields the list of captured logs"""
    plugin = request.config.pluginmanager.getplugin("loglady-plugin")
    assert isinstance(plugin, LogladyPlugin)

    capture = plugin.enable_fixture()
    yield capture.records
    plugin.disable_fixture()
