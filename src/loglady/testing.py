# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for testing with pytest"""

import sys
from collections.abc import Generator
from typing import Literal

import pytest

from . import _config_stack, config
from .destination import CaptureDestination, TextIODestination
from .manager import Manager
from .middleware import add_call_info
from .transport import SyncTransport
from .types import Record


def configure_for_tests(destination: Literal["stdout"] | Literal["capture"] = "stdout"):
    """Configures LogLady with the bare minimum for operating during tests.

    You can call this in conftest.py to make sure LogLady magics work throughout
    your codebase during tests.
    """

    if destination == "stdout":
        # We use a lazy proxy here to delay binding to sys.stdout as long
        # as possible, which makes it work correctly with stuff like pytest's
        # capsys.
        dest = TextIODestination(_ProxyLazyIO(lambda: sys.stdout))
    else:
        dest = CaptureDestination()

    manager = config.configure(
        transport=SyncTransport(),
        middleware=[add_call_info],
        destinations=[dest],
        install_hook=False,
    )

    return manager, dest


@pytest.fixture()
def loglady_stdout() -> Generator[Manager, None, None]:
    """A fixture that configures loglady for minimal output to stdout"""
    with _config_stack.rewind():
        m, _ = configure_for_tests("stdout")
        yield m


@pytest.fixture()
def loglady_capture() -> Generator[list[Record], None, None]:
    """A fixture that configures loglady for capturing all logs, yields the list of captured logs"""
    with _config_stack.rewind():
        _, cap = configure_for_tests("capture")
        assert isinstance(cap, CaptureDestination)
        with cap as cap_list:
            yield cap_list


class _ProxyLazyIO:
    def __init__(self, resolve):
        super().__init__()
        self.resolve = resolve

    def write(self, s: str, /) -> int:
        return self.resolve().write(s)

    def flush(self):
        return self.resolve().flush()
