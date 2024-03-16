# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from loglady import Record
from loglady.logger import Logger


class RelayStub:
    def __init__(self):
        super().__init__()
        self.records = []

    def __call__(self, record: Record) -> None:
        self.records.append(record)


def test_construct():
    relay = RelayStub()

    logger = Logger(relay=relay)
    assert logger.context == {}

    logger = Logger(relay=relay, context=dict(a=42))
    assert logger.context == dict(a=42)


def test_bind_unbind():
    relay = RelayStub()

    l_root = Logger(relay=relay)
    l1 = l_root.bind(a=42, b="two")
    l2 = l1.bind(a=43, c="three")
    l3 = l1.bind(a=None, d="four")

    assert l_root.context == {}
    assert l1.context == dict(a=42, b="two")
    assert l2.context == dict(a=43, b="two", c="three")
    assert l3.context == dict(a=None, b="two", d="four")

    l4 = l1.unbind("b", "d")
    assert l4.context == dict(a=42)
    assert l1.context != l4.context


def test_methods():
    relay = RelayStub()
    log = Logger(relay=relay)

    log.log("hello", a=42)
    assert relay.records.pop() == dict(msg="hello", a=42)
    log.debug("hello", a=43)
    assert relay.records.pop() == dict(msg="hello", level="debug", a=43)
    log.trace("hello", a=44)
    assert relay.records.pop() == dict(msg="hello", level="debug", stack_info=True, a=44)
    log.info("hello", a=45)
    assert relay.records.pop() == dict(msg="hello", level="info", a=45)
    log.warning("hello", a=46)
    assert relay.records.pop() == dict(msg="hello", level="warning", a=46)
    log.warn("hello", a=47)
    assert relay.records.pop() == dict(msg="hello", level="warning", a=47)
    log.success("hello", a=48)
    assert relay.records.pop() == dict(msg="hello", level="success", a=48)
    log.error("hello", a=49)
    assert relay.records.pop() == dict(msg="hello", level="error", a=49)
    log.exception("hello", a=50)
    assert relay.records.pop() == dict(msg="hello", level="error", exc_info=True, a=50)


def test_methods_with_context():
    relay = RelayStub()
    log = Logger(relay=relay).bind(context_a=42)

    log.log("hello")
    assert relay.records.pop() == dict(msg="hello", context_a=42)
