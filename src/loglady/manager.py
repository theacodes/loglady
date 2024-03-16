# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from .logger import Logger
from .transport import Transport
from .types import DestinationList, MiddlewareList, Record


class Manager:
    def __init__(
        self,
        *,
        transport: Transport,
        middleware: MiddlewareList,
        destinations: DestinationList,
    ):
        super().__init__()
        self.transport = transport
        self.middleware = middleware
        self.destinations = destinations

    @property
    def destinations(self) -> DestinationList:
        return self.transport.destinations

    @destinations.setter
    def destinations(self, val: DestinationList):
        self.transport.destinations = val

    def logger(self, **context):
        return Logger(relay=self.relay, context=context)

    def start(self):
        self.transport.start()

    def stop(self):
        self.transport.stop()

    def flush(self):
        self.transport.flush()

    def _apply_middleware(self, record: Record | None):
        for fn in self.middleware:
            if record is None:
                break
            record = fn(record)

        return record

    def relay(self, record: Record) -> None:
        processed_record = self._apply_middleware(record)
        if processed_record is None:
            return
        self.transport.relay(processed_record)
