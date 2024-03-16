# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from typing import override

import loglady
from loglady import Destination, Record

from .utils import assert_dict_subset


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
    assert_dict_subset(
        dest.records[0],
        dict(
            msg="hello, world!",
            level="info",
            timestamp=...,
            call_filename=...,
            call_fn=...,
            call_lineno=...,
            call_module=...,
            thread_id=...,
            thread_name=...,
        ),
    )
    assert_dict_subset(
        dest.records[1],
        dict(
            msg="Eek!",
            level="warning",
            more_stuff="...",
            timestamp=...,
            call_filename=...,
            call_fn=...,
            call_lineno=...,
            call_module=...,
            thread_id=...,
            thread_name=...,
        ),
    )
