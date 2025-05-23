# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

import contextlib
from collections import UserString
from collections.abc import Generator, Sequence
from io import StringIO
from typing import Literal, cast

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
        help="Disable deferred formatting of captured logs. Deferred formatting prevents unnecessarily formatting logs that are not ever seen, which can slow down tests.",
    )
    group.addoption(
        "--loglady-capture-limit",
        type=int,
        default=1000,
        help="Set the limit for captured logs. Having some limit here prevents wasted memory or CPU, which can slow down tests. Set negative to disable the limit.",
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

    @property
    def capture_limit(self) -> int | Literal[False]:
        limit = self.config.option.loglady_capture_limit
        return limit if limit >= 0 else False

    def start_global_capturing(self):
        self._global_captured = CaptureDestination(limit=self.capture_limit)
        self._manager = config.configure(
            transport=SyncTransport(),
            processors=config.DEFAULT_PROCESSORS,
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
        self._fixture_captured = CaptureDestination(limit=self.capture_limit)
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

    def grab_captured_output(self) -> str | None:
        if self._global_captured is None:
            return None

        capture = _DeferredCapturedOutput.create(self._global_captured)

        if capture.is_empty():
            return None

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
            if (captured := self.grab_captured_output()) is not None:
                # NOTE: The '*' in the key is load-bearing. Without it, pytest will try to use this section when
                # dropping into `--pdb`, but that doesn't handle the deferred rendering string correctly.
                item.add_report_section(when, "*loglady*", captured)

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
        failed_or_errored_tests = {
            report.nodeid for report in [*terminalreporter.getreports("failed"), *terminalreporter.getreports("error")]
        }

        for category, reports in terminalreporter.stats.items():
            for report in reports:
                if not hasattr(report, "sections"):
                    continue
                test_failed = report.nodeid in failed_or_errored_tests
                for n, (section, content) in enumerate(report.sections):
                    if isinstance(content, _DeferredCapturedOutput):
                        if test_failed:
                            report.sections[n] = (section, content.render(use_color=self.use_color))
                        else:
                            report.sections[n] = (
                                section,
                                f"{content.data} ({category=}, {section=}), {test_failed=}, {report.nodeid=})",
                            )

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

    def is_empty(self) -> bool:
        return self.captured is None or len(self.captured.records) == 0

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

        if self.captured.discarded_records > 0:
            io.write(
                f"\n**** Discarded {self.captured.discarded_records} records, use --loglady-capture-limit to control capture limits. ****\n"
            )

        self.captured = None
        self.rendered = io.getvalue()
        return self.rendered


@pytest.fixture
def loglady_capture(request: pytest.FixtureRequest) -> Generator[Sequence[Record], None, None]:
    """A fixture that captures global loglady logs and yields the list of captured logs"""
    plugin = request.config.pluginmanager.getplugin("loglady-plugin")
    assert isinstance(plugin, LogladyPlugin)

    capture = plugin.enable_fixture()
    yield capture.records
    plugin.disable_fixture()
