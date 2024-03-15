# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from ._rich import RichRenderer
from .logger import Logger
from .manager import Manager
from .middlewares import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp
from .transport import ThreadedTransport


def a_function(log):
    log.log("here's a stacktrace!", level="info", stack_info=True)


if __name__ == "__main__":
    dest = RichRenderer()
    tp = ThreadedTransport([dest])
    mgr = Manager(
        tp,
        middlewares=[
            add_timestamp,
            add_thread_info,
            add_exception_and_stack_info,
            add_call_info,
        ],
    )
    mgr.start()

    log = Logger(manager=mgr)
    log.log("hello", level="debug", a="42", thing=dict(key="value"))
    log.log("hello", level="info")
    log.log("hello", level="warning")
    log.log("hello", level="success")
    log.log("hello", level="error")

    l2 = log.bind(prefix="moop")
    l2.log(
        "hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello hello",
        level="debug",
        more_stuff="howdy",
    )
    l2.log("hello", level="info")
    l2.log("hello", level="warning")
    l2.log("hello", level="success")
    l2.log("hello", level="error")

    try:
        lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    except Exception:  # noqa: BLE001
        log.log("oops!", level="error", exc_info=True)

    l3 = log.bind(oh="no")
    l3.log("MORE")

    a_function(l3)

    mgr.stop()
