# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import loglady
from loglady import CompareRecord

from .stub_destination import StubDestination


def test_configure_and_magics():
    dest = StubDestination()
    mgr = loglady.configure(processors=[dest])

    loglady.info("hello, world!")

    l1 = loglady.bind(context=42)
    l1.warning("Eek!", more_stuff="...")

    mgr.flush()

    assert len(dest.records) == 2
    assert dest.records[0] == CompareRecord(message="hello, world!", level="info", context=dict())
    assert dest.records[1] == CompareRecord(message="Eek!", level="warning", context=dict(context=42, more_stuff="..."))
