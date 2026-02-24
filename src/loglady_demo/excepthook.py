# Copyright (c) 2026 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

# ruff: noqa: TRY003, EM101, B904, E722, RUF100, BLE001

import argparse

import rich.traceback

from loglady.excepthook import install_excepthook

from ._common import configure


def raise_original():
    err = ValueError("I'm the original exception!")
    err.add_note("I'm a note on the original exception.")
    err.add_note("I'm another note.")
    raise err


def demo_context():
    def raise_exception():
        try:
            raise_original()
        except:
            rerr = RuntimeError("I'm the exception raised in except!")
            rerr.add_note("I'm a note on the exception raised in except.")
            raise rerr

    raise_exception()


def demo_cause():
    def raise_exception():
        try:
            raise_original()
        except ValueError as err:
            rerr = RuntimeError("I'm the exception raised in except!")
            rerr.add_note("I'm a note on the exception raised in except.")
            raise rerr from err

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

    parser = argparse.ArgumentParser(description="Demo of loglady's excepthook with rich tracebacks.")
    parser.add_argument(
        "--demo",
        choices=["context", "cause", "group"],
        default="cause",
    )
    parser.add_argument(
        "--hook",
        choices=["sys", "rich", "loglady"],
        default="loglady",
    )

    args = parser.parse_args()

    match args.hook:
        case "sys":
            pass
        case "rich":
            rich.traceback.install()
        case "loglady":
            install_excepthook()
        case _:
            msg = f"Invalid hook choice: {args.hook!r}"
            raise ValueError(msg)

    match args.demo:
        case "context":
            demo_context()
        case "cause":
            demo_cause()
        case "group":
            demo_group()
        case _:
            msg = f"Invalid demo choice: {args.demo!r}"
            raise ValueError(msg)
