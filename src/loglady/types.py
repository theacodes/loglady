# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from collections.abc import Callable
from typing import Any

type Record = dict[str, Any]
type Context = Record
type Middleware = Callable[[Record], Record]
