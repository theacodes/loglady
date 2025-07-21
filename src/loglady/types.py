# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

import enum
from collections.abc import Callable, Sequence
from typing import Any

type Record = dict[str, Any]
type Context = Record
type Processor = Callable[[Record], Record | None]
type ProcessorList = Sequence[Processor]
type Relay = Callable[[Record], None]


class ReservedKeys(enum.StrEnum):
    msg = "msg"
    level = "level"
    prefix = "prefix"
    icon = "icon"
    timestamp = "timestamp"
    captured_thread_info = "__captured_thread_info"
    captured_exception = "__captured_exception"
    captured_stack = "__captured_stack"
    captured_call_info = "__captured_call_info"
