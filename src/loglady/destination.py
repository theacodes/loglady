# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from collections.abc import Callable

from .types import Record

type Destination = Callable[[Record], None]
