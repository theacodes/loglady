# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Fallback handles managing logs when loglady hasn't been explicitly configured."""

from __future__ import annotations

import sys
import typing
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal, override

from .destination import CaptureDestination, Destination, LazyDestination, TextIODestination
from .errors import InvalidFallbackModeError, NotConfiguredError
from .manager import Manager
from .processors import add_timestamp
from .transport import SyncTransport
from .types import Record
from .warnings import NotConfiguredWarning

FallbackMode = Literal["buffer", "stderr", "warn", "error"]


def validate_fallback_mode(mode: str) -> FallbackMode:
    mode = mode.lower()
    valid_options = typing.get_args(FallbackMode)
    if mode not in valid_options:
        raise InvalidFallbackModeError(mode=mode, valid_options=valid_options)
    return typing.cast(FallbackMode, mode)


@dataclass(slots=True, kw_only=True)
class Fallback:
    mode: Final[FallbackMode]

    _stderr_destination: Destination = field(init=False)
    _capture_destination: CaptureDestination = field(init=False)
    _warn_destination: _WarnDestination = field(init=False)
    _buffered_manager: Manager = field(init=False)
    _stderr_manager: Manager = field(init=False)
    _warn_manager: Manager = field(init=False)
    _error_manager: Manager = field(init=False)

    def __post_init__(self):
        self._stderr_destination = LazyDestination(lambda: TextIODestination(io=sys.stderr))
        self._capture_destination = CaptureDestination()
        self._warn_destination = _WarnDestination(
            msg="loglady.log() called before loglady.configure()", next_destination=self._stderr_destination
        )
        self._buffered_manager = Manager(
            transport=SyncTransport(self._capture_destination),
            processors=[add_timestamp],
        )
        self._stderr_manager = Manager(
            transport=SyncTransport(self._stderr_destination),
            processors=[],
        )
        self._warn_manager = Manager(
            transport=SyncTransport(self._warn_destination),
            processors=[],
        )
        self._error_manager = Manager(
            transport=SyncTransport(_ErrorDestination()),
            processors=[],
        )

    @property
    def manager(self):
        match self.mode:
            case "buffer":
                return self._buffered_manager
            case "stderr":
                return self._stderr_manager
            case "warn":
                return self._warn_manager
            case "error":
                return self._error_manager

    def flush(self):
        self.manager.flush()

    def drain_to_new_manager(self, manager: Manager):
        src = self._capture_destination
        if not src.records:
            return

        for record in src.records:
            manager.relay(record)

        src.reset()
        manager.flush()

    def drain_remaining_to_warn(self):
        self._warn_destination.msg = "program exited with buffered logs before loglady.configure() was called"
        self.drain_to_new_manager(self._warn_manager)


_WARNING_SKIP_PREFIXES = (str(Path(__file__).parent),)


class _WarnDestination(Destination):
    def __init__(self, msg: str, next_destination: Destination):
        super().__init__()
        self.msg = msg
        self.next_destination = next_destination
        self.has_warned = False

    @override
    def __call__(self, record: Record) -> None:
        if not self.has_warned:
            self.has_warned = True
            warnings.warn(
                NotConfiguredWarning(),
                skip_file_prefixes=_WARNING_SKIP_PREFIXES,
                stacklevel=2,
            )

        self.next_destination(record)


class _ErrorDestination(Destination):
    @override
    def __call__(self, record: Record) -> None:
        raise NotConfiguredError()
