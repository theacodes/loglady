# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from dataclasses import dataclass, field

from .logger import Logger
from .processor import Processor, flush, process
from .record import Record


@dataclass(kw_only=True, slots=True)
class Manager:
    """Wrangles all the bits of LogLady so that things work!

    Managers can be constructed directly, though typically you'll use `loglady.configure()` or `loglady.create_manager()`
    so that it gets globally registered as the active manager.

    A manager gives a `Logger` life: Any records created by a `Logger` are sent to the manager, when then handles
    sending them to the manager's processors.
    """

    processors: list[Processor] = field(default_factory=list)

    _logger_prototype: Logger = field(init=False)

    def __post_init__(
        self,
    ):
        self._logger_prototype = Logger(_send=self.send)

    def logger(self, name: str = "", **context):
        """Get a new Logger."""
        return self._logger_prototype.named(name).bind(**context)

    def flush(self):
        """Ask all processors to write any pending logs."""
        flush(self.processors)

    def send(self, record: Record) -> None:
        """Send a record by running it through all of the processors."""
        process(record, self.processors)
