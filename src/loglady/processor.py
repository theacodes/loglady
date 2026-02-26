# Copyright (c) 2026 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import copy
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Final, Protocol, override, runtime_checkable

from .errors import ProcessorError
from .record import Record


class Discard(Exception):  # noqa: N818
    """Raised or returned by a processor to indicate that the record should be discarded and not processed further."""


type ProcessorReturn = type[Discard] | Discard | Record | None


class Processor(Protocol):
    def __call__(self, record: Record) -> ProcessorReturn:
        """Takes a record and optionally modifies it or does something with it before handing it to the next processor.

        - If it returns or raises `Discard`, no further processors will be invoked.
        - If it returns a `Record`, that record will be passed to the next processor instead of the original.
        - If it returns any other value, including None, it will be ignored and the remaining processors will be passed
          the current record.
        """


@runtime_checkable
class Flushable(Protocol):
    def flush(self):
        """If this buffers output, flush it and block until all records have been processed."""
        return


def process(record: Record, processors: Iterable[Processor]):
    """Run a record through a list of processors."""
    for _ in iter_process(record, processors):
        pass


def iter_process(record: Record, processors: Iterable[Processor]) -> Iterable[Record]:
    """Run a record through a list of processors, yielding the processor and result after each processor.

    If a processor returns or raises `Discard`, the record will not be yielded and no further processors will be
    invoked.

    This is a low-level operation that is used by `process()` and advanced grouped processors to handle processor
    chains.
    """

    for processor in processors:
        try:
            result = processor(record)
        except Discard:
            return
        except Exception as err:
            raise ProcessorError(processor=processor) from err

        match result:
            case Discard():
                return
            case discard if discard is Discard:
                return
            case Record():
                record = result
                yield record
            case None:
                yield record
            case _:
                yield record

    return record


def flush(processors: Iterable[Processor]):
    """Ask all flushable processors in the chain to flush."""
    for processor in processors:
        if isinstance(processor, Flushable):
            processor.flush()


@dataclass(slots=True, frozen=True)
class group(Processor, Flushable):  # noqa: N801
    """A group of processors that can be treated as a single processor."""

    processors: Final[Sequence[Processor]]

    @override
    def __call__(self, record: Record) -> ProcessorReturn:
        return process(record, self.processors)

    @override
    def flush(self):
        return flush(self.processors)


@dataclass(slots=True, frozen=True)
class tee(group):  # noqa: N801
    """A processor that can be used to hand a record off to multiple processors.

    If `copy` is true, each processor will receive a copy of the record, so they can modify it without affecting
    other processors.

    If there's a processor after tee, it will receive the record after it's been processed by all the processors
    within the tee.
    """

    copy: bool = field(default=False, kw_only=True)

    @override
    def __call__(self, record: Record) -> ProcessorReturn:
        for processor in self.processors:
            if self.copy:
                record_ = copy.deepcopy(record)
            else:
                record_ = record

            processor(record_)

        return record
