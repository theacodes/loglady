# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import datetime
from decimal import Decimal

from ._rich import RichRenderer
from .logger import Logger
from .manager import Manager
from .middlewares import add_call_info, add_exception_and_stack_info, add_thread_info
from .transport import ThreadedTransport
from .types import Record

_counter = 0


def add_mock_timestamp(record: Record) -> Record:
    global _counter  # noqa: PLW0603
    record["timestamp"] = datetime.datetime(  # noqa: DTZ001
        year=2024,
        month=3,
        day=15,
        hour=0,
        minute=round(_counter),
        second=0,
    )
    _counter += 0.25
    return record


def demo_prefixes(log: Logger):
    l2 = log.bind(prefix="prefix")
    l2.debug("this is a debug message")
    l2.info("this one is an info message", icon="🡰")
    l2.warning("watch out, this one is a warning!", icon="🡲")
    l2.success("oh nice, this one is a success!", icon="✓")
    l2.error("oops, this one is an error", icon="🞷")


def demo_exc_and_stack(log: Logger):
    try:
        lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    except Exception:
        log.exception("this one has an exception attached")

    log.trace("& this one has a stacktrace!")


if __name__ == "__main__":
    dest = RichRenderer()
    tp = ThreadedTransport([dest])
    mgr = Manager(
        tp,
        middlewares=[
            add_mock_timestamp,
            add_thread_info,
            add_exception_and_stack_info,
            add_call_info,
        ],
    )
    mgr.start()

    log = Logger(manager=mgr)
    log.debug("this is a debug message")
    log.info("this one is an info message")
    log.warning("watch out, this one is a warning!")
    log.success("oh nice, this one is a success!")
    log.error("oops, this one is an error")

    log.info(
        "This one has structured data!",
        the_answer="42",
        thing=dict(key="value"),
        decimal=Decimal("3.14"),
        a_class=Manager,
    )

    log.info(
        """\
this one has a really really really really really long message that will get split over \
multiple lines. You are a worm through time. The thunder song distorts you. Happiness \
comes. White pearls, but yellow and red in the eye. Through a mirror, inverted is made \
right. Leave your insides by the door. Push the fingers through the surface into the \
wet. You've always been the new you. You want this to be true. We stand around you while \
you dream. You can almost hear our words but you forget. This happens more and more now. \
You gave us the permission in your regulations. We wait in the stains. The word that \
describes this is redacted. Repeat the word.""",
        it="also has",
        some=dict(data=42),
    )

    demo_prefixes(log)
    demo_exc_and_stack(log)

    mgr.stop()
