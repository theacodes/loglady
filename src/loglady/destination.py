# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from abc import ABC, abstractmethod

from .types import Record


class Destination(ABC):
    @abstractmethod
    def __call__(self, record: Record):
        raise NotImplementedError()
