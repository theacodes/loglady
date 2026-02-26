# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import queue
import threading
from dataclasses import dataclass, field
from typing import override
from warnings import warn

from .errors import ProcessorError
from .processor import flush, group, process
from .record import Record
from .warnings import BackgroundProcessorWarning, BackgroundThreadWarning, UndeliveredLogsWarning

_STOP = object()
_FLUSH = object()


@dataclass(slots=True, frozen=True)
class ThreadTransport(group):
    """A specialized processor that relays records to a background thread for further processing.

    This is useful for file, network, or console destinations that might block, since it allows the logging call to
    return immediately while the record is processed in the background.

    When used in a processor chain, it works similar to `tee` in that it passes the record through to the next
    processor, but also sends it to the background thread. It does not copy the record before sending, so it is
    possible for the record to be modified by later processors before it is processed in the background thread.
    """

    _q: queue.SimpleQueue = field(init=False, default_factory=queue.SimpleQueue)
    _thread: threading.Thread = field(init=False)
    _flush_cond: threading.Condition = field(init=False, default_factory=threading.Condition)

    def __post_init__(self):
        object.__setattr__(self, "_thread", threading.Thread(target=self._thread_main))
        self._thread.daemon = True

    @override
    def __call__(self, record: Record):
        self._q.put(record)

    def start(self):
        self._thread.start()

    # TODO: Add a timeout?
    def shutdown(self):
        if not self._thread.is_alive():
            return

        # TODO: Use queue.shutdown
        self._q.put(_STOP)
        self._thread.join()

        if not self._q.empty():
            warn(
                UndeliveredLogsWarning(remaining_logs=self._q.qsize()),
                stacklevel=1,
            )

        flush(self.processors)

    # TODO: Add a timeout
    @override
    def flush(self):
        if not self._thread.is_alive():
            return

        self._q.put(_FLUSH)

        with self._flush_cond:
            _ = self._flush_cond.wait()

    def _thread_main(self):
        while True:
            try:
                record = self._q.get(block=True)

                if record is _STOP:
                    break

                if record is _FLUSH:
                    flush(self.processors)

                    with self._flush_cond:
                        self._flush_cond.notify_all()

                    continue

                self._deliver(record)

            except (queue.Empty, queue.ShutDown):
                break

            except Exception as err:
                warn(
                    BackgroundThreadWarning(error=err),
                    stacklevel=1,
                )
                raise

    def _deliver(self, record: Record):
        try:
            process(record, self.processors)
        except ProcessorError as err:
            warn(BackgroundProcessorWarning(processor=err.processor, error=err), stacklevel=1)
