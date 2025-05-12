# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Sequence
from functools import cached_property
from typing import Protocol, override

from .types import Record


class Destination(ABC):
    """A destination is responsible for *outputting* a Record. They're the last link in the chain."""

    def flush(self):
        """If this destination buffers output, flush it and block until all records have been outputted."""
        return

    @abstractmethod
    def __call__(self, record: Record) -> None:
        """Output the given record to the destination."""
        raise NotImplementedError()


type DestinationList = Sequence[Destination]


type TextIODestinationFormatter = Callable[[Record], str]


class _TextIO(Protocol):
    """The very limited subset of TextIO that TextIODestination depends on."""

    def write(self, s: str, /) -> int: ...
    def flush(self) -> None: ...


class TextIODestination(Destination):
    """A simple destination that just outputs strings to a TextIO instance."""

    def __init__(self, io: _TextIO, formatter: TextIODestinationFormatter | None = None) -> None:
        super().__init__()
        self.io = io

        if formatter is None:
            formatter = PlainFormatter()
        self.formatter = formatter

    @override
    def __call__(self, record: Record) -> None:
        text = self.formatter(record)
        _ = self.io.write(text)

    @override
    def flush(self):
        self.io.flush()


class ReprFormatter:
    """A simple formatter that just uses repr() to format a record."""

    def __call__(self, record: Record) -> str:
        return f"{record!r}\n"


class PlainFormatter:
    """A simple formatter that formats the record as a string."""

    def __call__(self, record: Record) -> str:
        level = record.get("level", "notset")
        msg = record.pop("msg")
        return f"{level}: {msg} {record=!r}\n"


class CaptureDestination(Destination):
    """A simple destination that records all records."""

    def __init__(self, limit: int | None = None) -> None:
        super().__init__()
        self.limit: int | None = limit
        self.records: deque[Record] = deque(maxlen=limit)
        self.discarded_records: int = 0

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
        self.records = deque(maxlen=self.limit)
        self.discarded_records = 0

    def playback(self, *destinations: Destination):
        """Playback recorded records to all given destinations"""
        for record in self.records:
            for destination in destinations:
                destination(record)

    def __enter__(self):
        self.reset()
        return self.records

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()


class LazyDestination(Destination):
    """A destination that wraps another destination, only creating it when
    actually needed."""

    def __init__(self, factory: Callable[[], Destination]):
        super().__init__()
        self._factory = factory

    @cached_property
    def _wrapped(self):
        return self._factory()

    @override
    def __call__(self, record: Record) -> None:
        self._wrapped(record)

    @override
    def flush(self):
        return super().flush()
