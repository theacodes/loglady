# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import queue
import threading
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from typing import ClassVar, Protocol, override
from warnings import warn

from .destination import Destination, DestinationList
from .types import Record
from .warnings import BackgroundThreadWarning, DestinationErrorWarning, UndeliveredLogsWarning


class Transport(Protocol):
    """Transports are responsible for relaying records to a list of destinations"""

    destinations: Destination | DestinationList

    def relay(self, record: Record) -> None: ...
    def flush(self) -> None: ...
    def shutdown(self) -> None:
        pass


@dataclass(slots=True)
class SyncTransport(Transport):
    """A very simple transport that immediately delivers enqueued records to destinations.

    This is useful for tests but not recommended for real applications.
    """

    destinations: Destination | DestinationList = field(default_factory=list)

    @override
    def relay(self, record: Record) -> None:
        for dest in _iter_destinations(self.destinations):
            dest(record)

    @override
    def flush(self) -> None:
        for dest in _iter_destinations(self.destinations):
            dest.flush()


@dataclass(slots=True)
class ThreadedTransport(Transport):
    """A transport that handles relaying in a separate thread.

    This prevents logging calls from blocking, as they only need to queue the record.
    """

    _STOP: ClassVar = object()
    _FLUSH: ClassVar = object()

    destinations: Destination | DestinationList = field(default_factory=list)

    _q: queue.SimpleQueue = field(init=False, default_factory=queue.SimpleQueue)
    _thread: threading.Thread | None = field(init=False, default=None)
    _flush_cond: threading.Condition = field(init=False, default_factory=threading.Condition)

    @override
    def relay(self, record: Record):
        self._q.put(record)

    def start(self):
        self._thread = threading.Thread(target=self._thread_main)
        self._thread.daemon = True
        self._thread.start()

    @override
    def shutdown(self):
        if self._thread is None:
            return

        self._q.put(self._STOP)
        self._thread.join()
        self._thread = None

        if not self._q.empty():
            warn(
                UndeliveredLogsWarning(remaining_logs=self._q.qsize()),
                stacklevel=1,
            )

    @override
    def flush(self):
        if self._thread is None:
            return

        self._q.put(self._FLUSH)

        with self._flush_cond:
            _ = self._flush_cond.wait()

        for destination in _iter_destinations(self.destinations):
            destination.flush()

    def _thread_main(self):
        while True:
            try:
                record = self._q.get(block=True)
                if record is self._STOP:
                    break

                if record is self._FLUSH:
                    with self._flush_cond:
                        self._flush_cond.notify_all()
                    continue

                self._deliver(record)

            except queue.Empty:
                break

            except Exception as err:
                warn(
                    BackgroundThreadWarning(error=err),
                    stacklevel=1,
                )
                raise

    def _deliver(self, record: Record):
        for dest in _iter_destinations(self.destinations):
            try:
                dest(record)
            except Exception as err:  # noqa: BLE001
                warn(DestinationErrorWarning(destination=dest, error=err), stacklevel=1)


def _iter_destinations(destination: Destination | DestinationList) -> Generator[Destination]:
    """Helper to ensure that we always have a list of destinations"""
    if isinstance(destination, Iterable):
        yield from destination
        return
    yield destination
