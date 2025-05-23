# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Fallback handles managing logs when loglady hasn't been configured."""

import os
import sys
import warnings
from pathlib import Path
from typing import Literal, override

from .destination import CaptureDestination, Destination, LazyDestination, TextIODestination
from .manager import Manager
from .processors import add_timestamp
from .transport import SyncTransport
from .types import Record

FALLBACK_MODE = os.environ.get("LOGLADY_FALLBACK_MODE", "stderr")

FallbackMode = Literal["buffer", "stderr", "warn", "error"]


class Fallback:
    def __init__(self, mode: FallbackMode | str | None = None):
        super().__init__()
        if mode is None:
            mode = FALLBACK_MODE

        self.mode = mode
        self.stderr_destination = LazyDestination(lambda: TextIODestination(sys.stderr))
        self.capture_destination = CaptureDestination()
        self.warn_destination = _WarnDestination(
            msg="loglady.log() called before loglady.configure()", next_destination=self.stderr_destination
        )
        self.buffered_manager = Manager(
            transport=SyncTransport(),
            processors=[add_timestamp],
            destinations=[self.capture_destination],
        )
        self.stderr_manager = Manager(
            transport=SyncTransport(),
            processors=[],
            destinations=[self.stderr_destination],
        )
        self.warn_manager = Manager(
            transport=SyncTransport(),
            processors=[],
            destinations=[self.warn_destination],
        )
        self.error_manager = Manager(
            transport=SyncTransport(),
            processors=[],
            destinations=[_ErrorDestination()],
        )

    @property
    def manager(self):
        match self.mode:
            case "buffer":
                return self.buffered_manager
            case "stderr":
                return self.stderr_manager
            case "warn":
                return self.warn_manager
            case "error":
                return self.error_manager
            case _:
                msg = f"fallback mode must be one of 'buffer', 'stderr', 'warn', or 'error', got {self.mode}"
                raise ValueError(msg)

    def drain_to_new_manager(self, manager: Manager):
        src = self.capture_destination
        if not src.records:
            return

        for record in src.records:
            manager.relay(record)

        src.reset()
        manager.flush()

    def drain_remaining_to_warn(self):
        self.warn_destination.msg = "program exited with buffered logs before loglady.configure() was called"
        self.drain_to_new_manager(self.warn_manager)


class NotConfiguredWarning(RuntimeWarning):
    pass


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
                self.msg,
                NotConfiguredWarning,
                skip_file_prefixes=_WARNING_SKIP_PREFIXES,
                stacklevel=2,
            )

        self.next_destination(record)


class NotConfiguredError(RuntimeError):
    pass


class _ErrorDestination(Destination):
    @override
    def __call__(self, record: Record) -> None:
        msg = "loglady.log() called before loglady.configure()"
        raise NotConfiguredError(msg)
