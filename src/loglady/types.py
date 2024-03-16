# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

type Record = dict[str, Any]
type Context = Record
type Middleware = Callable[[Record], Record | None]


class Destination(ABC):
    @abstractmethod
    def __call__(self, record: Record):
        raise NotImplementedError()
