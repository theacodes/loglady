# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for threading"""

import collections
import threading

# Note: this list is chosen based on how easy it is to tell the emoji apart and how well they display on a terminal.
_EMOJI = list(
    "👽🤖🎃🥶🦷👂👀👤🧶🧵🧦🧤🎩👑💍🌂🏀🏈🎾🎱🏓🪃🪁🏹🥊🛹🛼🥌🏆🥇🎪🎭🎨🎬🎤🎧🪇🥁🎷🎺🪗🎸🪕🎻🎲🎳🎮🧩🚗🛞🚀🛸🚁🛶🛟🗿🎡🎠💾💿📼📷🧭⏰📡💡🔦💎🪚🧲🔮💈🦠🧽🧸🎁🎈🎀🪭🪩📦📯📁📎🩷💮🌀📣🍏🍐🍊🍋🍌🍉🍇🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🫛🥦🥬🫑🌽🥕🧄🧅🥐🍞🥖🥨🧀🥚🥓🥩🍖🦴🌭🍔🍟🍕🥪🌮🌯🥗🥫🍣🥟🦪🍤🍚🍥🥠🍡🍨🍦🥧🧁🍰🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🫖🧃🧊🥡🧂🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐽🐸🐵🐔🐧🐦🪿🦆🦉🦇🐺🐗🐴🦄🫎🐝🪱🐛🦋🐌🐞🐜🪲🦂🐢🐍🦎🦖🦕🐙🪼🦐🦞🦀🐡🐠🐟🐬🐳🦈🦭🐊🦍🦧🐩🐓🦃🦤🦚🦜🦢🦩🐇🦝🦨🦡🦫🦦🦥🐁🐀🦔🐉"
)

_thread_id_to_emoji = collections.OrderedDict()


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
    # number of emojis being used. Instead, we do this nonsense.

    if thread_id in _thread_id_to_emoji:
        return _thread_id_to_emoji[thread_id]

    _thread_id_to_emoji[thread_id] = _EMOJI[len(_thread_id_to_emoji) % len(_EMOJI)]

    # This limits the size of the dictionary.
    while len(_thread_id_to_emoji) > len(_EMOJI):
        _ = _thread_id_to_emoji.popitem(last=False)

    return _thread_id_to_emoji[thread_id]
