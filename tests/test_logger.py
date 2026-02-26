# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from loglady import CapturedFrame, CompareRecord, Logger, Record


class RelayStub:
    def __init__(self):
        super().__init__()
        self.records = []

    def __call__(self, record: Record) -> None:
        self.records.append(record)


def test_construct():
    relay = RelayStub()

    logger = Logger(_send=relay)
    assert logger.context == {}

    logger = Logger(_send=relay, _context=dict(a=42))
    assert logger.context == dict(a=42)


def test_bind_unbind():
    relay = RelayStub()

    l_root = Logger(_send=relay)
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


def test_prefix_suffix():
    relay = RelayStub()
    l_root = Logger(_send=relay)
    l1 = l_root.prefixed("pre")
    l2 = l1.suffixed("suf")
    l3 = l2.prefixed("new-root")

    assert l_root.name == ""
    assert l1.name == "pre"
    assert l2.name == "pre.suf"
    assert l3.name == "new-root.pre.suf"


def test_div_operator_name():
    relay = RelayStub()
    l_root = Logger(_name="parent", _send=relay)
    l1 = l_root / "child"
    l2 = l1 / "grandchild"

    assert l_root.name == "parent"
    assert l1.name == "parent.child"
    assert l2.name == "parent.child.grandchild"


def test_div_operator_context():
    relay = RelayStub()
    l_root = Logger(_name="parent", _send=relay)
    l1 = l_root / dict(a=42)
    l2 = l1 / dict(b="two")

    assert l_root.context == dict()
    assert l1.context == dict(a=42)
    assert l2.context == dict(a=42, b="two")


def test_methods():
    relay = RelayStub()
    log = Logger(_send=relay)

    log.log("hello", a=42)
    assert relay.records.pop() == CompareRecord(message="hello", context=dict(a=42))
    log.debug("hello", a=43)
    assert relay.records.pop() == CompareRecord(message="hello", level="debug", context=dict(a=43))
    log.info("hello", a=45)
    assert relay.records.pop() == CompareRecord(message="hello", level="info", context=dict(a=45))
    log.warning("hello", a=46)
    assert relay.records.pop() == CompareRecord(message="hello", level="warning", context=dict(a=46))
    log.warn("hello", a=47)
    assert relay.records.pop() == CompareRecord(message="hello", level="warning", context=dict(a=47))
    log.success("hello", a=48)
    assert relay.records.pop() == CompareRecord(message="hello", level="success", context=dict(a=48))
    log.error("hello", a=49)
    assert relay.records.pop() == CompareRecord(message="hello", level="error", context=dict(a=49))


def test_exception():
    relay = RelayStub()
    log = Logger(_send=relay)

    # No exception current set, should just return the record as-is
    log.exception("hmm")
    assert relay.records.pop() == CompareRecord(message="hmm", level="error")

    # Explicitly passing an exception instance
    err = ValueError("hrm")
    log.exception(err)
    record = relay.records.pop()
    assert record.message == ""
    captured = record.exception
    assert captured.string == "hrm"
    assert captured.type == "ValueError"

    # Passing in both a message and an error instance
    log.exception("oh, no!", err)  # noqa: PLE1205
    record = relay.records.pop()
    assert record.message == "oh, no!"
    captured = record.exception
    assert captured.string == "hrm"
    assert captured.type == "ValueError"

    # Getting the exception from context.
    try:
        raise ValueError("oops")  # noqa: EM101, TRY301
    except ValueError:
        log.exception()

    record = relay.records.pop()
    assert record.message == ""
    captured = record.exception
    assert captured.string == "oops"
    assert captured.type == "ValueError"

    # Getting the exception from context with a message
    try:
        raise ValueError("oops")  # noqa: EM101, TRY301
    except ValueError:
        log.exception("oh, no!")

    record = relay.records.pop()
    assert record.message == "oh, no!"
    captured = record.exception
    assert captured.string == "oops"
    assert captured.type == "ValueError"


def test_trace():
    relay = RelayStub()
    log = Logger(_send=relay)

    log.trace("hmm")
    record = relay.records.pop()
    assert record.message == "hmm"
    stack = record.stack
    first = stack[0]
    assert isinstance(first, CapturedFrame)


def test_methods_with_context():
    relay = RelayStub()
    log = Logger(_send=relay).bind(a=42)

    log.log("hello")
    assert relay.records.pop() == CompareRecord(message="hello", context=dict(a=42))
