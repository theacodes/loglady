# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import contextlib
from collections.abc import Generator
from io import StringIO

import pytest
import rich

import loglady
import loglady._config_stack
from loglady.destination import CaptureDestination
from loglady.rich.destination import RichConsoleDestination
from loglady.transport import SyncTransport
from loglady.types import Record


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    _ = config.pluginmanager.register(LogladyPlugin(config), "loglady-plugin")


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

    def start_global_capturing(self):
        self._global_captured = CaptureDestination()
        self._manager = loglady.config.configure(
            transport=SyncTransport(),
            middleware=loglady.config.DEFAULT_MIDDLEWARE,
            destinations=[self._global_captured],
            install_hook=False,
            once=False,
        )

    def stop_global_capturing(self):
        if self._manager is None:
            return

        self._manager.flush()
        self._manager.stop()
        _ = loglady._config_stack.pop()

    def read_global_capture(self):
        if self._global_captured is None:
            return ""

        if not self._global_captured.records:
            return ""

        io = StringIO()
        use_color = self.config.option.color != "no"
        console = rich.console.Console(
            file=io,
            force_terminal=use_color,
            force_interactive=False,
            force_jupyter=False,
        )
        console_dest = RichConsoleDestination(console=console)

        self._global_captured.playback(console_dest)

        return io.getvalue()

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

    @contextlib.contextmanager
    def item_capture(self, when: str, item: pytest.Item) -> Generator[None]:
        self.start_global_capturing()
        self.activate_fixture()
        try:
            yield
        finally:
            self.deactivate_fixture()
            self.stop_global_capturing()

            out = self.read_global_capture()
            item.add_report_section(when, "loglady", out)

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

    @pytest.hookimpl(tryfirst=True)
    def pytest_keyboard_interrupt(self) -> None:
        self.stop_global_capturing()

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(self) -> None:
        self.stop_global_capturing()


@pytest.fixture
def loglady_capture(request: pytest.FixtureRequest) -> Generator[list[Record], None, None]:
    """A fixture that captures global loglady logs and yields the list of captured logs"""
    plugin = request.config.pluginmanager.getplugin("loglady-plugin")
    assert isinstance(plugin, LogladyPlugin)

    capture = plugin.enable_fixture()
    yield capture.records
    plugin.disable_fixture()
