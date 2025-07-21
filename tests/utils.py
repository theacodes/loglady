# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import dataclasses
from dataclasses import Field
from typing import Any, ClassVar, Protocol, runtime_checkable


@runtime_checkable
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


def assert_dict_subset(actual, expected):
    """Compares two dictionaries but only checks the keys found in *expected*.

    Also allows specifying ... as the value in the expected dictionary to accept any value in the actual as long as the
    key is present.
    """
    __tracebackhide__ = True

    if isinstance(actual, DataclassInstance):
        actual = dataclasses.asdict(actual)

    for k, rv in expected.items():
        assert k in actual, f"{k!r} not found in actual, expected actual[{k!r}] == {rv!r}. actual:\n{actual!r}"

        lv = actual[k]

        if rv == ...:
            continue

        assert lv == rv, f"expected actual[{k!r}] == {rv!r}, found {lv!r}"
