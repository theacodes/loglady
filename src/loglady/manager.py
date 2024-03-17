# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from .destination import DestinationList
from .logger import Logger
from .transport import Transport
from .types import MiddlewareList, Record


class Manager:
    """Wrangles all the bits of LogLady so that things work!

    Managers can be constructed directly, though typically you'll use
    loglady.configure() so that it gets globally registered as the active
    manager.

    A manager gives a Logger life: Any records created by a Logger are sent to
    the manager. The manager runs the record through middleware and then hands
    it off to the transport. The transport is responsible for sending the record
    to all destinations.

    Managers are responsible for the lifetime of its Transport and Destinations.
    If you're manually creating managers, don't forget to call start() and
    stop().
    """

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
        """Get a new Logger"""
        return Logger(relay=self.relay, context=context)

    def start(self):
        """Tell the transport to start"""
        self.transport.start()

    def stop(self):
        """Flush all destinations and stop the transport"""
        self.flush()
        self.transport.stop()

    def flush(self):
        """Ask all destinations to write any pending logs"""
        self.transport.flush()

    def _apply_middleware(self, record: Record | None):
        for fn in self.middleware:
            if record is None:
                break
            record = fn(record)

        return record

    def relay(self, record: Record) -> None:
        """Run a record through middleware and hand it off to the transport"""
        processed_record = self._apply_middleware(record)
        if processed_record is None:
            return
        self.transport.relay(processed_record)
