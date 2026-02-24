# Copyright (c) 2026 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

# ruff: noqa: TRY003, EM101, B904, E722, RUF100

from decimal import Decimal

import loglady

from ._common import LONG, configure


def demo_basics():
    log = loglady.logger()
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


def demo_magics():
    loglady.debug("via magic loglady.debug")
    loglady.info("via magic loglady.info")
    loglady.warning("via magic loglady.warning")
    loglady.success("via magic loglady.success")
    loglady.error("via magic loglady.error")


def demo_prefixes():
    l2 = loglady.prefix(prefix="prefix")
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
    l2.info("& you can use rich markup, like emoji :ok: and [green]color[/]!")


class DemoCallsite:
    def __call__(self):
        def inner():
            loglady.info("this log message is nestled deep!")

        inner()


if __name__ == "__main__":
    configure()
    demo_basics()
    demo_magics()
    demo_prefixes()
    DemoCallsite()()
