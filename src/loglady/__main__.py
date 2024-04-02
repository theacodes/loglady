# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Demo for LogLady

Run using:
    python3 -m loglady
"""

import datetime
from decimal import Decimal

import loglady

_counter = 0


def add_mock_timestamp(record: loglady.Record) -> loglady.Record:
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


def demo_prefixes(log: loglady.Logger):
    l2 = log.prefix("prefix")
    l2.debug("there's a", icon=">")
    l2.info("bunch of neat", icon="->")
    l2.warning("icons that can be!", icon="<-")
    l2.success("used with prefix!", icon="o")
    l2.error("including arrows, marks, and other fun bits!", icon="...")
    l2.debug("there's a", icon="v")
    l2.info("bunch of neat", icon="x")
    l2.warning("icons that can be!", icon="*")
    l2.success("used with prefix!", icon="**")
    l2.error("including arrows, marks, and other fun bits!", icon="+")
    l2.debug("there's a", icon="s")
    l2.info("bunch of neat", icon="p")
    l2.warning("icons that can be!", icon="!!")
    l2.success("used with prefix!", icon="??")
    l2.error("including arrows, marks, and other fun bits!", icon="?!")
    l2.debug("there's a", icon="<3")
    l2.info("bunch of neat", icon=":)")
    l2.warning("icons that can be!", icon=":(")
    l2.success("used with prefix!", icon="f")
    l2.error("including arrows, marks, and other fun bits!", icon="snow")


def demo_magics():
    loglady.debug("via magic loglady.debug")
    loglady.info("via magic loglady.info")
    loglady.warning("via magic loglady.warning")
    loglady.success("via magic loglady.success")
    loglady.error("via magic loglady.error")


def demo_exc_and_stack(log: loglady.Logger):
    try:
        lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
    except Exception:
        log.exception("this one has an exception attached")

    log.trace("& this one has a stacktrace!")


def demo_catcher(log: loglady.Logger):
    with log.catch(msg="this catches exceptions with a context manager"):
        lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821


class DemoCallsite:
    def __call__(self):
        def inner():
            log.info("this log message is nestled deep!")

        inner()


if __name__ == "__main__":
    mgr = loglady.configure(
        middleware=[*loglady.DEFAULT_MIDDLEWARE, add_mock_timestamp],
    )

    log = mgr.logger()
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
        a_class=loglady.Logger,
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

    demo_magics()
    DemoCallsite()()
    demo_prefixes(log)
    demo_exc_and_stack(log)
    demo_catcher(log)
