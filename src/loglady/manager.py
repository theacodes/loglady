# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from collections.abc import Sequence

from .destination import Destination
from .transport import Transport
from .types import Middleware, Record


class Manager:
    def __init__(
        self,
        *,
        transport: Transport,
        middleware: list[Middleware],
        destinations: list[Destination],
    ):
        super().__init__()
        self.transport = transport
        self.middleware = middleware
        self.destinations = destinations

    @property
    def destinations(self) -> Sequence[Destination]:
        return self.transport.destinations

    @destinations.setter
    def destinations(self, val: Sequence[Destination]):
        self.transport.destinations = val

    def start(self):
        self.transport.start()

    def stop(self):
        self.transport.stop()

    def _apply_middleware(self, record: Record | None):
        for fn in self.middleware:
            if record is None:
                break
            record = fn(record)

        return record

    def relay(self, record: Record):
        processed_record = self._apply_middleware(record)
        if processed_record is None:
            return
        self.transport.relay(processed_record)
