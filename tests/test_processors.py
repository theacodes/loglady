# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from types import FrameType

import loglady.processors
from loglady.types import SysExcInfo


def test_add_stack_info():
    record = loglady.processors.add_exception_and_stack_info(dict(stack_info=True))

    stack: FrameType | None = record.get("stacktrace")
    assert stack is not None
    assert stack.f_globals.get("__file__") == __file__


def test_add_exception_info():
    record = dict(exc_info=True)
    err = RuntimeError()

    try:
        raise err
    except RuntimeError:
        record = loglady.processors.add_exception_and_stack_info(record)

    excinfo: SysExcInfo | None = record.get("exception")
    assert excinfo is not None

    exc_type, exc, traceback = excinfo

    assert exc_type is RuntimeError
    assert exc == err
    assert traceback is not None


def test_add_call_info():
    record = loglady.processors.add_call_info(dict())

    assert record.get("call_fn") == "test_add_call_info"
    assert record.get("call_filename") == __file__
    assert record.get("call_module") == __name__


def test_add_call_info_with_invisible_fn():
    def invisible_fn():
        __tracebackhide__ = True
        return loglady.processors.add_call_info(dict())

    record = invisible_fn()

    assert record.get("call_fn") == "test_add_call_info_with_invisible_fn"
    assert record.get("call_filename") == __file__
    assert record.get("call_module") == __name__
