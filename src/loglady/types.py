# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

from collections.abc import Callable, Sequence
from types import TracebackType
from typing import Any

type Record = dict[str, Any]
type Context = Record
type Middleware = Callable[[Record], Record | None]
type MiddlewareList = Sequence[Middleware]
type Relay = Callable[[Record], None]
type SysExcInfo = tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None]
