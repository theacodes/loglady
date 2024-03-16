# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import queue
import threading
from abc import ABC, abstractmethod
from typing import override
from warnings import warn

from .types import DestinationList, Record


class Transport(ABC):
    destinations: DestinationList = ()

    def __init__(self):
        super().__init__()

    @abstractmethod
    def relay(self, record: Record) -> None:
        raise NotImplementedError()

    def process(self, record: Record) -> None:
        for dest in self.destinations:
            dest(record)

    def start(self) -> None:
        return

    def stop(self) -> None:
        return

    def flush(self) -> None:
        return


class SyncTransport(Transport):
    @override
    def relay(self, record: Record) -> None:
        self.process(record)


class ThreadedTransport(Transport):
    _STOP = object()
    _FLUSH = object()

    def __init__(self):
        super().__init__()
        self._q = queue.SimpleQueue()
        self._thread: threading.Thread | None = None
        self._flush_cond = threading.Condition()

    @override
    def relay(self, record: Record):
        self._q.put(record)

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

                self.process(record)

            except queue.Empty:
                break

    @override
    def start(self):
        self._thread = threading.Thread(target=self._thread_main)
        self._thread.daemon = True
        self._thread.start()

    @override
    def stop(self):
        if self._thread is None:
            return

        self._q.put(self._STOP)
        self._thread.join()
        self._thread = None

        self._q.put({})

        if not self._q.empty():
            warn(
                f"logging thread exited with {self._q.qsize()} logs not yet processed",
                stacklevel=1,
            )

    @override
    def flush(self):
        if self._thread is None:
            return

        self._q.put(self._FLUSH)

        with self._flush_cond:
            _ = self._flush_cond.wait()
