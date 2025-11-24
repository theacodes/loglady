# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from loglady import Record
from loglady.exception_capture import CapturedException, CapturedFrame
from loglady.logger import Logger
from loglady.types import ReservedKeys


class RelayStub:
    def __init__(self):
        super().__init__()
        self.records = []

    def __call__(self, record: Record) -> None:
        self.records.append(record)


def test_construct():
    relay = RelayStub()

    logger = Logger(_relay=relay)
    assert logger.context == {}

    logger = Logger(_relay=relay, _context=dict(a=42))
    assert logger.context == dict(a=42)


def test_bind_unbind():
    relay = RelayStub()

    l_root = Logger(_relay=relay)
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
    log = Logger(_relay=relay)

    log.log("hello", a=42)
    assert relay.records.pop() == dict(msg="hello", a=42)
    log.debug("hello", a=43)
    assert relay.records.pop() == dict(msg="hello", level="debug", a=43)
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


def test_exception():
    relay = RelayStub()
    log = Logger(_relay=relay)

    # No exception current set, should just return the record as-is
    log.exception("hmm")
    assert relay.records.pop() == dict(msg="hmm", level="error")

    # Explicitly passing an exception instance
    err = ValueError("hrm")
    log.exception(err)
    record = relay.records.pop()
    assert record["msg"] == ""
    captured: CapturedException = record[ReservedKeys.captured_exception]
    assert captured.string == "hrm"
    assert captured.type == "ValueError"

    # Passing in both a message and an error instance
    log.exception("oh, no!", err)  # noqa: PLE1205
    record = relay.records.pop()
    assert record["msg"] == "oh, no!"
    captured: CapturedException = record[ReservedKeys.captured_exception]
    assert captured.string == "hrm"
    assert captured.type == "ValueError"

    # Getting the exception from context.
    try:
        raise ValueError("oops")  # noqa: EM101, TRY301
    except ValueError:
        log.exception()

    record = relay.records.pop()
    assert record["msg"] == ""
    captured: CapturedException = record[ReservedKeys.captured_exception]
    assert captured.string == "oops"
    assert captured.type == "ValueError"

    # Getting the exception from context with a message
    try:
        raise ValueError("oops")  # noqa: EM101, TRY301
    except ValueError:
        log.exception("oh, no!")

    record = relay.records.pop()
    assert record["msg"] == "oh, no!"
    captured: CapturedException = record[ReservedKeys.captured_exception]
    assert captured.string == "oops"
    assert captured.type == "ValueError"


def test_trace():
    relay = RelayStub()
    log = Logger(_relay=relay)

    log.trace("hmm")
    record = relay.records.pop()
    assert record["msg"] == "hmm"
    stack = record[ReservedKeys.captured_stack]
    first = stack[0]
    assert isinstance(first, CapturedFrame)


def test_methods_with_context():
    relay = RelayStub()
    log = Logger(_relay=relay).bind(context_a=42)

    log.log("hello")
    assert relay.records.pop() == dict(msg="hello", context_a=42)
