# Copyright (c) 2026 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

# ruff: noqa: TRY003, EM101, B904, E722, RUF100, BLE001

import loglady

from ._common import configure


def demo_exc_and_stack():
    def grandparent_with_exception():
        def parent():
            def child():
                lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821

            child()

        parent()

    try:
        grandparent_with_exception()
    except Exception:
        loglady.exception("this one has an exception attached")

    def grandparent_with_trace():
        def parent():
            def child():
                loglady.trace("& this one has a stacktrace!")

            child()

        parent()

    grandparent_with_trace()


def demo_catcher():
    with loglady.catch(message="this catches exceptions with a context manager"):
        lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821


def demo_context():
    def raise_original():
        raise ValueError("I'm the original exception!")

    def raise_exception():
        try:
            raise_original()
        except:
            raise RuntimeError("I'm the exception raised in except!")

    try:
        raise_exception()
    except:
        loglady.exception("this exception will have a context")


def demo_cause():
    def raise_original():
        raise ValueError("I'm the original exception!")

    def raise_exception():
        try:
            raise_original()
        except ValueError as err:
            raise RuntimeError("I'm the exception raised in except!") from err

    try:
        raise_exception()
    except Exception:
        loglady.exception("this exception will have a cause")


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

    try:
        raise err_group
    except ExceptionGroup:
        loglady.exception("this one will have an exception group.")


if __name__ == "__main__":
    configure()
    demo_exc_and_stack()
    demo_catcher()
    demo_context()
    demo_cause()
    demo_group()
    loglady.info("done!")
