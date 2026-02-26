# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

import sys
from collections import deque
from collections.abc import Callable
from dataclasses import InitVar, dataclass, field
from typing import Final, Protocol, override

from .processor import Flushable, Processor, process
from .record import Record

type TextIODestinationFormatter = Callable[[Record], str]


class _TextIO(Protocol):
    """The very limited subset of TextIO that TextIODestination depends on."""

    def write(self, s: str, /) -> int: ...
    def flush(self) -> None: ...


@dataclass(slots=True, kw_only=True)
class TextIODestination(Processor, Flushable):
    """A simple destination that just outputs strings to a TextIO instance."""

    io: _TextIO
    formatter: TextIODestinationFormatter = field(default_factory=lambda: PlainFormatter())

    @override
    def __call__(self, record: Record) -> None:
        text = self.formatter(record)
        _ = self.io.write(text)

    @override
    def flush(self):
        self.io.flush()


def stderr_destination(formatter: TextIODestinationFormatter | None = None) -> TextIODestination:
    """Create a TextIODestination that writes to stderr."""
    return TextIODestination(io=sys.stderr, formatter=formatter or PlainFormatter())


class ReprFormatter:
    """A simple formatter that just uses repr() to format a record."""

    def __call__(self, record: Record) -> str:
        return f"{record!r}\n"


class PlainFormatter:
    """A simple formatter that formats the record as a string."""

    def __call__(self, record: Record) -> str:
        level = record.level
        context = f"{record.context!r}" if record.context else None
        ts = record.timestamp.isoformat() if record.timestamp else None
        parts = [record.name, level, record.message, context, ts]
        return f"{' '.join(filter(None, parts))}\n"


@dataclass(slots=True, kw_only=True)
class CaptureDestination(Processor):
    """A simple destination that records all records."""

    limit: InitVar[int | None] = None
    records: deque[Record] = field(init=False)
    discarded_records: int = field(init=False, default=0)

    def __post_init__(self, limit: int | None) -> None:
        self.records: deque[Record] = deque(maxlen=limit)

    @override
    def __call__(self, record: Record) -> None:
        """Capture the record. If the limit is reached, discard the oldest record."""
        current_len = len(self.records)
        self.records.append(record)

        # If the length didn't change, we discarded a record
        if len(self.records) == current_len:
            self.discarded_records += 1

    def reset(self):
        """Clear all captured records"""
        self.records.clear()
        self.discarded_records = 0

    def playback(self, *processors: Processor):
        """Playback recorded records into the given processors."""
        for record in self.records:
            process(record, processors)

    def __enter__(self):
        self.reset()
        return self.records

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()


@dataclass(slots=True, kw_only=True)
class LazyDestination(Processor):
    """A destination that wraps another processor, only creating it when actually needed."""

    factory: Final[Callable[[], Processor]]

    _instance: Processor | None = field(init=False, default=None, repr=False)

    @override
    def __call__(self, record: Record) -> None:
        if self._instance is None:
            self._instance = self.factory()

        self._instance(record)
