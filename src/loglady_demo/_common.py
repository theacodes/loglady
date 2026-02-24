# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import datetime

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


LONG = """You are a worm through time. The thunder song distorts you. Happiness \
comes. White pearls, but yellow and red in the eye. Through a mirror, inverted is made \
right. Leave your insides by the door. Push the fingers through the surface into the \
wet. You've always been the new you. You want this to be true. We stand around you while \
you dream. You can almost hear our words but you forget. This happens more and more now. \
You gave us the permission in your regulations. We wait in the stains. The word that \
describes this is redacted. Repeat the word."""


def configure():
    loglady.configure(
        processors=[*loglady.DEFAULT_PROCESSORS, add_mock_timestamp],
    )
