# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


def assert_dict_subset(actual, expected):
    """Compares two dictionaries but only checks the keys found in *expected*.

    Also allows specifying ... as the value in the expected dictionary to accept any value in the actual as long as the
    key is present.
    """
    __tracebackhide__ = True

    for k, rv in expected.items():
        try:
            lv = actual[k]
        except KeyError as err:
            msg = f'"{k}" not found in actual, expected actual["{k}"]=={rv!r}'
            raise AssertionError() from err

        if rv == ...:
            continue

        if lv != rv:
            msg = f'expected actual["{k}"]=={rv!r}, found {lv!r}'
            raise AssertionError(msg)
