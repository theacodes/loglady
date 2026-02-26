# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from dataclasses import dataclass, field
from typing import override

from loglady import Processor, Record


@dataclass
class StubDestination(Processor):
    records: list[Record] = field(default_factory=list)

    @override
    def __call__(self, record: Record):
        self.records.append(record)
