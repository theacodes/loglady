# Copyright (c) 2026 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from dataclasses import dataclass, field, fields
from datetime import datetime
from types import EllipsisType
from typing import override

from .exception_capture import CapturedException
from .stack_capture import CapturedFrame, CapturedStack
from .thread_capture import CapturedThreadInfo

type Context = dict[str, object]


@dataclass(kw_only=True, slots=True)
class Record:
    message: str
    name: str | None = None
    level: str | None = None
    context: Context = field(default_factory=dict)

    timestamp: datetime | None = None
    caller: CapturedFrame | None = None
    thread: CapturedThreadInfo | None = None
    exception: CapturedException | None = None
    stack: CapturedStack | None = None

    def __setitem__(self, key: str, value: object) -> None:
        self.context[key] = value

    def __getitem__(self, key):
        return self.context[key]

    def get(self, key, default=None):
        return self.context.get(key, default)

    def items(self):
        return self.context.items()

    def keys(self):
        return self.context.keys()


@dataclass(kw_only=True, slots=True, frozen=True)
class CompareRecord:
    """Used to check the contents of a record in tests. Any field unspecified or set to `...` will be ignored in the comparison."""

    message: str | EllipsisType = ...
    name: str | None | EllipsisType = ...
    level: str | None | EllipsisType = ...
    context: Context | EllipsisType = ...

    timestamp: datetime | None | EllipsisType = ...
    caller: CapturedFrame | None | EllipsisType = ...
    thread: CapturedThreadInfo | None | EllipsisType = ...
    exception: CapturedException | None | EllipsisType = ...
    stack: CapturedStack | None | EllipsisType = ...

    @override
    def __eq__(self, other):
        if not isinstance(other, Record):
            return NotImplemented

        for field_def in fields(self):
            expected_value = getattr(self, field_def.name)
            if expected_value is ...:
                continue

            actual_value = getattr(other, field_def.name)
            if expected_value != actual_value:
                return False

        return True

    @override
    def __hash__(self) -> int:
        return object.__hash__(self)
