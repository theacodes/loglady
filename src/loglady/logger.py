# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Self

from .types import Context, Relay


class Logger:
    def __init__(self, *, relay: Relay, context: Context | None = None):
        super().__init__()
        self._relay = relay
        self._context = context if context is not None else {}

    @property
    def context(self) -> Mapping[str, Any]:
        return MappingProxyType(self._context)

    def log(self, msg, **record: Any) -> None:
        rec = self._context.copy()
        rec.update(**record)
        rec["msg"] = msg

        self._relay(rec)

    def trace(self, msg, **record: Any) -> None:
        self.log(msg, level="debug", stack_info=True, **record)

    def debug(self, msg, **record: Any) -> None:
        self.log(msg, level="debug", **record)

    def info(self, msg, **record: Any) -> None:
        self.log(msg, level="info", **record)

    def warning(self, msg, **record: Any) -> None:
        self.log(msg, level="warning", **record)

    warn = warning

    def success(self, msg, **record: Any) -> None:
        self.log(msg, level="success", **record)

    def error(self, msg, **record: Any) -> None:
        self.log(msg, level="error", **record)

    def exception(self, msg, **record: Any) -> None:
        self.log(msg, level="error", exc_info=True, **record)

    def bind(self, **context: Any) -> Self:
        ctx = self._context.copy()
        ctx.update(**context)
        return self.__class__(relay=self._relay, context=ctx)

    def unbind(self, *keys: str) -> Self:
        inst = self.bind()
        for key in keys:
            inst._context.pop(key, None)
        return inst
