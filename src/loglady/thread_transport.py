# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from __future__ import annotations

import atexit
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, override
from warnings import warn

from .errors import ProcessorError
from .processor import flush, group, process
from .record import Record
from .warnings import LogladyWarning

_ACTIVE_TRANSPORTS: set[ThreadTransport] = set()
_STOP = object()
_FLUSH = object()


@dataclass(slots=True, frozen=True, repr=False)
class ThreadTransport(group):
    """A specialized processor that relays records to a background thread for further processing.

    This is useful for file, network, or console destinations that might block, since it allows the logging call to
    return immediately while the record is processed in the background.

    When used in a processor chain, it works similar to `tee` in that it passes the record through to the next
    processor, but also sends it to the background thread. It does not copy the record before sending, so it is
    possible for the record to be modified by later processors before it is processed in the background thread.
    """

    flush_timeout: float = field(default=5.0, kw_only=True)
    shutdown_timeout: float = field(default=5.0, kw_only=True)

    _num: int = field(init=False, default_factory=lambda: len(_ACTIVE_TRANSPORTS) + 1)
    _q: queue.SimpleQueue = field(init=False, default_factory=queue.SimpleQueue)
    _thread: threading.Thread = field(init=False)
    _flush_cond: threading.Condition = field(init=False, default_factory=threading.Condition)

    def __post_init__(self):
        object.__setattr__(
            self,
            "_thread",
            threading.Thread(
                target=self._thread_main,
                daemon=True,
                name=f"loglady-{self._num}",
            ),
        )
        _ACTIVE_TRANSPORTS.add(self)
        self._thread.start()

    @override
    def __hash__(self):
        return object.__hash__(self)

    @override
    def __call__(self, record: Record):
        self._q.put(record)

    @property
    def name(self) -> str:
        return self._thread.name

    def shutdown(self):
        try:
            if not self._thread.is_alive():
                return

            self._q.put(_STOP)

            self._thread.join(self.shutdown_timeout)

            if self._thread.is_alive():
                warn(
                    ShutdownTimeoutWarning(
                        name=self.name,
                        timeout=self.shutdown_timeout,
                    ),
                    stacklevel=1,
                )

            if not self._q.empty():
                warn(
                    UndeliveredLogsWarning(
                        name=self.name,
                        remaining_logs=self._q.qsize(),
                    ),
                    stacklevel=1,
                )

            flush(self.processors)

        finally:
            _ACTIVE_TRANSPORTS.discard(self)

    @override
    def flush(self):
        if not self._thread.is_alive():
            return

        self._q.put(_FLUSH)

        with self._flush_cond:
            if not self._flush_cond.wait(timeout=self.flush_timeout):
                warn(
                    FlushTimeoutWarning(
                        name=self.name,
                        timeout=self.flush_timeout,
                    ),
                    stacklevel=1,
                )

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
                    UnexpectedErrorWarning(name=self.name, error=err),
                    stacklevel=1,
                )
                raise

    def _deliver(self, record: Record):
        try:
            process(record, self.processors)
        except ProcessorError as err:
            warn(
                ProcessorErroredWarning(
                    name=self.name,
                    processor=err.processor,
                    error=err,
                ),
                stacklevel=1,
            )


@atexit.register
def _shutdown_thread_transports():  # pyright: ignore[reportUnusedFunction]
    for transport in list(_ACTIVE_TRANSPORTS):
        transport.shutdown()


class UnexpectedErrorWarning(LogladyWarning):
    def __init__(self, *, name: str, error: Exception) -> None:
        super().__init__(f"logging thread '{name}' shutdown due to unexpected error: {error!r}")


class UndeliveredLogsWarning(LogladyWarning):
    def __init__(self, *, name: str, remaining_logs: int) -> None:
        super().__init__(f"logging thread '{name}' shutdown with {remaining_logs} logs undelivered.")


class ProcessorErroredWarning(LogladyWarning):
    def __init__(self, *, name: str, processor: Any, error: Exception) -> None:
        super().__init__(f"error in logging thread '{name}' while running processor {processor!r}: {error!r}")


class FlushTimeoutWarning(LogladyWarning):
    def __init__(self, *, name: str, timeout: float) -> None:
        super().__init__(f"logging thread '{name}' did not flush within {timeout} seconds.")


class ShutdownTimeoutWarning(LogladyWarning):
    def __init__(self, *, name: str, timeout: float) -> None:
        super().__init__(f"logging thread '{name}' did not shut down within {timeout} seconds.")
