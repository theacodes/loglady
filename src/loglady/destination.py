# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from functools import cached_property
from io import StringIO
from typing import TextIO, override

from .types import Record


class Destination(ABC):
    def flush(self):
        return

    @abstractmethod
    def __call__(self, record: Record) -> None:
        raise NotImplementedError()


type DestinationList = Sequence[Destination]


type Formatter = Callable[[Record], str]


class TextIODestination(Destination):
    def __init__(self, io: TextIO, formatter: Formatter | None = None) -> None:
        super().__init__()
        self.io = io

        if formatter is None:
            formatter = PrintFormatter()
        self.formatter = formatter

    @override
    def __call__(self, record: Record) -> None:
        text = self.formatter(record)
        _ = self.io.write(text)

    @override
    def flush(self):
        self.io.flush()


class PrintFormatter:
    def __call__(self, record: Record) -> str:
        out = StringIO()
        print(record, file=out)
        return out.getvalue()


class CaptureDestination(Destination):
    def __init__(self):
        super().__init__()
        self.records = []

    @override
    def __call__(self, record: Record) -> None:
        self.records.append(record)

    def reset(self):
        self.records = []

    def __enter__(self):
        self.reset()
        return self.records

    def __exit__(self, exc_type, exc_value, traceback):
        self.reset()


class LazyDestination(Destination):
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
