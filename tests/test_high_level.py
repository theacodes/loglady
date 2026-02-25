# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from typing import override

import loglady
from loglady import CompareRecord, Destination, Record


class StubDestination(Destination):
    def __init__(self):
        super().__init__()
        self.records = []

    @override
    def __call__(self, record: Record):
        self.records.append(record)


def test_configure_and_magics():
    dest = StubDestination()
    mgr = loglady.configure(destinations=[dest])

    loglady.info("hello, world!")

    l1 = loglady.bind(context=42)
    l1.warning("Eek!", more_stuff="...")

    mgr.flush()

    assert len(dest.records) == 2
    assert dest.records[0] == CompareRecord(message="hello, world!", level="info", context=dict())
    assert dest.records[1] == CompareRecord(message="Eek!", level="warning", context=dict(context=42, more_stuff="..."))
