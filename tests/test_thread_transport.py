# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from loglady import Record, ThreadTransport

from .stub_destination import StubDestination


def test_threaded_transport():
    dest = StubDestination()
    transp = ThreadTransport(processors=[dest])

    record = Record(message="hello")

    transp(record)

    # Not yet processed, so it shouldn't be in the destination.
    assert len(dest.records) == 0

    # Start the thread, flush, and check again.
    transp.start()
    transp.flush()

    assert dest.records.pop() is record

    transp.shutdown()
