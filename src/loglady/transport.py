# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import queue
import threading
from abc import ABC, abstractmethod
from typing import override

from .destination import Destination
from .types import Record


class AbstractTransport(ABC):
    destinations: list[Destination]

    def __init__(self, *, destinations: list[Destination]):
        super().__init__()
        self.destinations = destinations

    @abstractmethod
    def relay(self, record: Record):
        raise NotImplementedError()

    def process(self, record: Record):
        for dest in self.destinations:
            dest(record)

    def start(self):
        pass

    def stop(self):
        pass

class SyncTransport(AbstractTransport):
    @override
    def relay(self, record: Record):
        self.process(record)

class ThreadedTransport(AbstractTransport):
    _STOP = object()

    def __init__(self, destinations: list["Destination"]):
        super().__init__(destinations=destinations)
        self._q = queue.SimpleQueue()
        self._thread: threading.Thread | None = None

    @override
    def relay(self, record: Record):
        self._q.put(record, block=False)

    def _thread_main(self):
        while True:
            try:
                record = self._q.get(block=True)
                if record is self._STOP:
                    break

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

        self._q.put(self._STOP, block=False)
        self._thread.join()
        self._thread = None
