# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

# ruff: noqa: TRY003, EM101, B904, E722

"""Demo for LogLady

Run using:
    python3 -m loglady
"""

import datetime
from decimal import Decimal

import loglady

_counter: float = 0


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
    def grandparent_with_exception():
        def parent():
            def child():
                lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821

            child()

        parent()

    try:
        grandparent_with_exception()
    except Exception:
        log.exception("this one has an exception attached")

    def grandparent_with_trace():
        def parent():
            def child():
                log.trace("& this one has a stacktrace!")

            child()

        parent()

    grandparent_with_trace()


def demo_catcher(log: loglady.Logger):
    with log.catch(msg="this catches exceptions with a context manager"):
        lol_this_wont_work()  # pyright: ignore[reportUndefinedVariable]  # noqa: F821


class DemoCallsite:
    def __call__(self):
        def inner():
            log.info("this log message is nestled deep!")

        inner()


def demo_context(log: loglady.Logger):
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
        log.exception("this exception will have a context")


def demo_cause(log: loglady.Logger):
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
        log.exception("this exception will have a cause")


def demo_group(log: loglady.Logger):
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
        errs.append(err)
    try:
        raise_err2()
    except ValueError as err:
        errs.append(err)

    err_group = ExceptionGroup("I'm the group", errs)

    try:
        raise err_group
    except ExceptionGroup:
        log.exception("this one will have an exception group.")


LONG = """You are a worm through time. The thunder song distorts you. Happiness \
comes. White pearls, but yellow and red in the eye. Through a mirror, inverted is made \
right. Leave your insides by the door. Push the fingers through the surface into the \
wet. You've always been the new you. You want this to be true. We stand around you while \
you dream. You can almost hear our words but you forget. This happens more and more now. \
You gave us the permission in your regulations. We wait in the stains. The word that \
describes this is redacted. Repeat the word."""

if __name__ == "__main__":
    mgr = loglady.configure(
        processors=[*loglady.DEFAULT_PROCESSORS, add_mock_timestamp],
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
        f"""\
this one has a really really really really really long message that will get split over \
multiple lines. {LONG}.""",
        it="also has",
        some=dict(data=42),
    )

    log.info(
        "And this one has a normal length message but structured data that's really long",
        long_str=LONG,
        long_dict={"key": LONG, "key2": LONG},
        long_list=[1, 2, LONG, LONG, LONG],
        long_nested=[1, 2, [3, 4, LONG, [5, 6, [7, 8, LONG, LONG], 9], 10], 11],
    )

    demo_magics()
    DemoCallsite()()
    demo_prefixes(log)
    demo_exc_and_stack(log)
    demo_catcher(log)
    demo_context(log)
    demo_cause(log)
    demo_group(log)
