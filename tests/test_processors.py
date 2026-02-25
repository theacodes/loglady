# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from loglady import CapturedFrame, Record, processors


def test_add_call_info():
    record = processors.add_call_info(Record(message="hello"))

    info = record.caller
    assert isinstance(info, CapturedFrame)
    assert info.qualname == "test_add_call_info"
    assert info.module_name == __name__
    assert info.filename == __file__


def test_add_call_info_with_invisible_fn():
    def invisible_fn():
        __tracebackhide__ = True
        return processors.add_call_info(Record(message="hello"))

    record = invisible_fn()

    info = record.caller
    assert isinstance(info, CapturedFrame)
    assert info.qualname == "test_add_call_info_with_invisible_fn"
    assert info.module_name == __name__
    assert info.filename == __file__
