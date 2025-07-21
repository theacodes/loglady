# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import loglady.processors
from loglady.exception_capture import CapturedFrame
from loglady.types import ReservedKeys


def test_add_call_info():
    record = loglady.processors.add_call_info(dict())

    info = record.get(ReservedKeys.captured_call_info)
    assert isinstance(info, CapturedFrame)
    assert info.qualname == "test_add_call_info"
    assert info.module_name == __name__
    assert info.filename == __file__


def test_add_call_info_with_invisible_fn():
    def invisible_fn():
        __tracebackhide__ = True
        return loglady.processors.add_call_info(dict())

    record = invisible_fn()

    info = record.get(ReservedKeys.captured_call_info)
    assert isinstance(info, CapturedFrame)
    assert info.qualname == "test_add_call_info_with_invisible_fn"
    assert info.module_name == __name__
    assert info.filename == __file__
