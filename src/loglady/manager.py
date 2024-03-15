# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from .transport import AbstractTransport
from .types import Middleware, Record


class Manager:
    def __init__(self, transport: AbstractTransport, middlewares: list[Middleware]):
        super().__init__()
        self.transport = transport
        self.middlewares = middlewares

    def start(self):
        self.transport.start()

    def stop(self):
        self.transport.stop()

    def relay(self, record: Record):
        for fn in self.middlewares:
            record = fn(record)

        self.transport.relay(record)
