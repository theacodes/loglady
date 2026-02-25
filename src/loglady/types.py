# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

from collections.abc import Callable, Sequence

from .record import Record

type Processor = Callable[[Record], Record | None]
type ProcessorList = Sequence[Processor]
type Relay = Callable[[Record], None]
