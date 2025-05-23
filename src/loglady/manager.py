# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from dataclasses import dataclass, field

from .logger import Logger
from .transport import Transport
from .types import ProcessorList, Record


@dataclass(kw_only=True, slots=True)
class Manager:
    """Wrangles all the bits of LogLady so that things work!

    Managers can be constructed directly, though typically you'll use
    loglady.configure() so that it gets globally registered as the active
    manager.

    A manager gives a Logger life: Any records created by a Logger are sent to
    the manager. The manager runs the record through processors and then hands
    it off to the transport. The transport is responsible for sending the record
    to all destinations.

    Managers are responsible for the lifetime of its Transport and Destinations.
    If you're manually creating managers, don't forget to call start() and
    stop().
    """

    transport: Transport
    processors: ProcessorList
    _logger_prototype: Logger = field(init=False)

    def __post_init__(
        self,
    ):
        self._logger_prototype = Logger(_relay=self.relay)

    def logger(self, **context):
        """Get a new Logger"""
        return self._logger_prototype.bind(**context)

    def flush(self):
        """Ask all destinations to write any pending logs"""
        self.transport.flush()

    def _apply_processors(self, record: Record | None):
        for fn in self.processors:
            if record is None:
                break
            record = fn(record)

        return record

    def relay(self, record: Record) -> None:
        """Run a record through processors and hand it off to the transport"""
        processed_record = self._apply_processors(record)
        if processed_record is None:
            return
        self.transport.relay(processed_record)

    def shutdown(self):
        self.transport.flush()
        self.transport.shutdown()
