# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for capturing thread information."""

import threading
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True, frozen=True)
class CapturedThreadInfo:
    name: str
    ident: int | None
    native_id: int | None
    is_main_thread: bool
    is_alive: bool
    is_daemonic: bool

    @property
    def emoji(self) -> str:
        return thread_emoji(self.ident)

    @classmethod
    def create(cls, thread: threading.Thread | None = None):
        if thread is None:
            thread = threading.current_thread()

        return cls(
            name=thread.name,
            ident=thread.ident,
            native_id=thread.native_id,
            is_main_thread=thread == threading.main_thread(),
            is_alive=thread.is_alive(),
            is_daemonic=thread.daemon,
        )


# Note: this list is chosen based on how easy it is to tell the emoji apart and how well they display on a terminal.
_EMOJI = list(
    "👽🤖🎃🥶🦷👂👀👤🧶🧵🧦🧤🎩👑💍🌂🏀🏈🎾🎱🏓🪃🪁🏹🥊🛹🛼🥌🏆🥇🎪🎭🎨🎬🎤🎧🪇🥁🎷🎺🪗🎸🪕🎻🎲🎳🎮🧩🚗🛞🚀🛸🚁🛶🛟🗿🎡🎠💾💿📼📷🧭⏰📡💡🔦💎🪚🧲🔮💈🦠🧽🧸🎁🎈🎀🪭🪩📦📯📁📎🩷💮🌀📣🍏🍐🍊🍋🍌🍉🍇🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🫛🥦🥬🫑🌽🥕🧄🧅🥐🍞🥖🥨🧀🥚🥓🥩🍖🦴🌭🍔🍟🍕🥪🌮🌯🥗🥫🍣🥟🦪🍤🍚🍥🥠🍡🍨🍦🥧🧁🍰🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🫖🧃🧊🥡🧂🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐽🐸🐵🐔🐧🐦🪿🦆🦉🦇🐺🐗🐴🦄🫎🐝🪱🐛🦋🐌🐞🐜🪲🦂🐢🐍🦎🦖🦕🐙🪼🦐🦞🦀🐡🐠🐟🐬🐳🦈🦭🐊🦍🦧🐩🐓🦃🦤🦚🦜🦢🦩🐇🦝🦨🦡🦫🦦🦥🐁🐀🦔🐉"
)


def thread_emoji(thread_id: int | threading.Thread | None = None):
    """Cute little helper that assigns each thread a unique emoji."""
    if isinstance(thread_id, threading.Thread):
        thread_id = thread_id.ident

    if thread_id is None:
        thread_id = threading.get_ident()

    is_main_thread = thread_id == threading.main_thread().ident

    if is_main_thread:
        return "⭐️"

    # Note: this used to just use the thread_id to index into the _EMOJI list with modulo, however, it turns out that
    # thread ids can sometime be evenly spaced which ruins all the fun of modulo indexing, leading to only a very small
    # number of emojis being used. Instead, we modulo the *hash* of the id.

    hashed_id = hash(thread_id)
    return _EMOJI[hashed_id % len(_EMOJI)]
