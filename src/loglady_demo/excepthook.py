# Copyright (c) 2026 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

# ruff: noqa: TRY003, EM101, B904, E722, RUF100, BLE001

from ._common import configure


def demo_context():
    def raise_original():
        raise ValueError("I'm the original exception!")

    def raise_exception():
        try:
            raise_original()
        except:
            raise RuntimeError("I'm the exception raised in except!")

    raise_exception()


def demo_cause():
    def raise_original():
        raise ValueError("I'm the original exception!")

    def raise_exception():
        try:
            raise_original()
        except ValueError as err:
            raise RuntimeError("I'm the exception raised in except!") from err

    raise_exception()


def demo_group():
    def raise_err1():
        def inner_raise_err1():
            raise ValueError("I'm the first error")

        return inner_raise_err1()

    def raise_err2():
        def inner_raise_err2():
            raise ValueError("I'm the second error")

        return inner_raise_err2()

    errs = []
    try:
        raise_err1()
    except ValueError as err:
        err.add_note("this is a note on the first error")
        errs.append(err)
    try:
        raise_err2()
    except ValueError as err:
        err.add_note("this is a note on the second error")
        errs.append(err)

    err_group = ExceptionGroup("I'm the group", errs)

    raise err_group


if __name__ == "__main__":
    configure()
    demo_context()
    # demo_cause()
    # demo_group()
