# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Fallback handles managing logs when loglady hasn't been explicitly configured."""

from __future__ import annotations

import os
import typing
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal, override

from .destinations import CaptureDestination, stderr_destination
from .errors import InvalidFallbackModeError, NotConfiguredError
from .manager import Manager
from .processor import Processor
from .processors import add_timestamp
from .record import Record
from .warnings import NotConfiguredWarning

FallbackMode = Literal["buffer", "stderr", "warn", "error"]


def environ_fallback_mode() -> FallbackMode:
    mode = os.environ.get("LOGLADY_FALLBACK_MODE", "stderr")
    mode = mode.lower()

    valid_options = typing.get_args(FallbackMode)
    if mode not in valid_options:
        raise InvalidFallbackModeError(mode=mode, valid_options=valid_options)

    return typing.cast(FallbackMode, mode)


@dataclass(slots=True, kw_only=True)
class Fallback:
    mode: Final[FallbackMode] = field(default_factory=environ_fallback_mode)

    _manager: Manager = field(init=False)
    _buffered: Final[CaptureDestination] = field(init=False, default_factory=CaptureDestination)

    def __post_init__(self):
        match self.mode:
            case "buffer":
                self._manager = Manager(processors=[add_timestamp, self._buffered])
            case "stderr":
                self._manager = Manager(processors=[stderr_destination()])
            case "warn":
                self._manager = Manager(processors=[_Warner(), stderr_destination()])
            case "error":
                self._manager = Manager(processors=[_Raiser()])

    @property
    def manager(self) -> Manager:
        return self._manager

    def flush(self):
        self.manager.flush()

    def drain_to(self, manager: Manager):
        src = self._buffered
        if not src.records:
            return

        for record in src.records:
            manager.send(record)

        src.reset()
        manager.flush()

    def warn_buffered(self):
        self.drain_to(
            Manager(
                processors=[
                    _Warner(
                        message="program exited with buffered logs before loglady.configure() was called",
                    ),
                    stderr_destination(),
                ]
            )
        )


_WARNING_SKIP_PREFIXES = (str(Path(__file__).parent),)


@dataclass(slots=True, kw_only=True)
class _Warner(Processor):
    message: Final[str] = "loglady.log() called before loglady.configure() was called"
    _has_warned: bool = False

    @override
    def __call__(self, record: Record) -> None:
        if self._has_warned:
            return

        self._has_warned = True

        warnings.warn(
            NotConfiguredWarning(),
            skip_file_prefixes=_WARNING_SKIP_PREFIXES,
            stacklevel=2,
        )


class _Raiser(Processor):
    @override
    def __call__(self, record: Record) -> None:
        raise NotConfiguredError()
