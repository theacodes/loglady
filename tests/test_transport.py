# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from typing import override

from loglady import Destination, Record
from loglady.transport import SyncTransport, ThreadedTransport


class StubDestination(Destination):
    def __init__(self):
        super().__init__()
        self.records = []

    @override
    def __call__(self, record: Record):
        self.records.append(record)


def test_sync_transport():
    transp = SyncTransport()
    record = dict(a=42, b="hello!")

    # No destinations, shouldn't do anything but also shouldn't error.
    transp.relay(record)

    dest = StubDestination()
    transp.destinations = [dest]

    transp.relay(record)

    assert dest.records.pop() == dict(a=42, b="hello!")


def test_threaded_transport():
    transp = ThreadedTransport()
    dest = StubDestination()
    transp.destinations = [dest]

    record = dict(a=42, b="hello!")

    transp.relay(record)

    # Not yet processed, so it shouldn't be in the destination.
    assert len(dest.records) == 0

    # Start the thread, flush, and check again.
    transp.start()
    transp.flush()

    assert dest.records.pop() == dict(a=42, b="hello!")

    transp.stop()
