# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

type Record = dict[str, Any]
type Context = Record
type Middleware = Callable[[Record], Record | None]
type MiddlewareList = Sequence[Middleware]
type DestinationList = Sequence[Destination]


class Destination(ABC):
    @abstractmethod
    def __call__(self, record: Record):
        raise NotImplementedError()
