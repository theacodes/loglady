# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from typing import Any

from .manager import Manager
from .types import Context, Record


class Logger:
    def __init__(self, *, manager: Manager, context: Context | None = None):
        super().__init__()
        self._manager = manager
        self._context = context if context is not None else {}

    def log(self, msg, **record: Any):
        rec = self._context.copy()
        rec.update(**record)
        rec["msg"] = msg

        self._manager.relay(rec)

    def bind(self, **context):
        ctx = self._context.copy()
        ctx.update(**context)
        return self.__class__(manager=self._manager, context=ctx)

    def unbind(self, *keys: str):
        inst = self.bind()
        for key in keys:
            inst._context.pop(key, None)
        return inst
