# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import asyncio
import functools
from types import FrameType

from loglady.stack_capture import (
    CapturedFrame,
    ElidedFrame,
    is_frame_from_site_packages,
    stack,
)


def test_infer_caller_naked():
    caller = CapturedFrame.create_from_caller()
    assert caller is not None
    assert caller.name.startswith("pytest_"), "Expected caller name to start with 'pytest_'"


def _infer_caller_thunk(**kwargs) -> CapturedFrame | None:
    return CapturedFrame.create_from_caller(**kwargs)


def test_infer_caller_inner():
    caller = _infer_caller_thunk()
    assert caller is not None
    assert caller.filename == __file__
    assert caller.name == "test_infer_caller_inner"


def test_infer_caller_with_partial():
    # functools.partial should not appear in the caller inference, regardless of if stdlib is included or not since
    # functools.partial uses a highly-optimized C implementation that causes it to not appear in the stack.
    caller = functools.partial(_infer_caller_thunk)()
    assert caller is not None
    assert caller.filename == __file__
    assert caller.name == "test_infer_caller_with_partial"


def test_infer_caller_from_stdlib():
    # Using asyncio a round-about way to get the stdlib to call our thunk, ensuring that we have frames from the stdlib
    # in the stack between the test function and the thunk. The stack will look like this:
    #   - test_infer_caller_from_stdlib
    #   - asyncio.run()
    #   - asyncio machinery
    #   - async_thunk()
    #   - infer_caller()
    # We want `infer_caller` to walk all the back back to `test_infer_caller_from_stdlib`, skipping all of the stdlib
    # frames in between.

    async def async_thunk(**kwargs):
        return CapturedFrame.create_from_caller(**kwargs)

    caller = asyncio.run(async_thunk())
    assert caller is not None
    assert caller.filename == __file__
    assert caller.name == "test_infer_caller_from_stdlib"

    # Do the same thing, but include the stdlib frames. This should now stop somewhere in the asyncio machinery.
    caller = asyncio.run(async_thunk(include_stdlib=True))
    assert caller is not None
    assert caller.filename is not __file__


def _stack_thunk(**kwargs) -> list[FrameType | ElidedFrame]:
    return list(stack(**kwargs))


def test_stack():
    stack = _stack_thunk()

    assert len(stack)

    # Include_elided is False, so all items should be stack frames
    assert all(isinstance(frame, FrameType) for frame in stack)

    # The most recent frame should be the test file.
    assert isinstance(stack[0], FrameType)
    assert stack[0].f_code.co_filename == __file__


def test_stack_with_predicate():
    unfiltered_stack = _stack_thunk()

    # exclude frames from site-packages, which should be in the stack because of pytest.
    def predicate(frame):
        return not (is_frame_from_site_packages(frame))

    filtered_stack = _stack_thunk(predicate=predicate)

    assert unfiltered_stack != filtered_stack

    # Include_elided is False, so all items should be stack frames
    assert all(isinstance(frame, FrameType) for frame in filtered_stack)

    # The most recent frame should be the test file.
    assert isinstance(filtered_stack[0], FrameType)
    assert filtered_stack[0].f_code.co_filename == __file__


def test_stack_with_include_elided():
    def predicate(frame):
        return not (is_frame_from_site_packages(frame))

    stack = _stack_thunk(predicate=predicate, include_elided=True)

    # The stack should have both elided and non-elided items.
    assert any(isinstance(frame, FrameType) for frame in stack)
    assert any(isinstance(frame, ElidedFrame) for frame in stack)
