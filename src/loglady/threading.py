# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Helpers for threading"""

import threading

# Note: this list is chosen based on how easy it is to tell the emoji apart and how well they display on a terminal.
_EMOJI = list(
    "👽🤖🎃🥶🦷👂👀👤🧶🧵🧦🧤🎩👑💍🌂🏀🏈🎾🎱🏓🪃🪁🏹🥊🛹🛼🥌🏆🥇🎪🎭🎨🎬🎤🎧🪇🥁🎷🎺🪗🎸🪕🎻🎲🎳🎮🧩🚗🛞🚀🛸🚁🛶🛟🗿🎡🎠💾💿📼📷🧭⏰📡💡🔦💎🪚🧲🔮💈🦠🧽🧸🎁🎈🎀🪭🪩📦📯📁📎🩷💮🌀📣🍏🍐🍊🍋🍌🍉🍇🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆🥑🫛🥦🥬🫑🌽🥕🧄🧅🥐🍞🥖🥨🧀🥚🥓🥩🍖🦴🌭🍔🍟🍕🥪🌮🌯🥗🥫🍣🥟🦪🍤🍚🍥🥠🍡🍨🍦🥧🧁🍰🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🫖🧃🧊🥡🧂🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐽🐸🐵🐔🐧🐦🪿🦆🦉🦇🐺🐗🐴🦄🫎🐝🪱🐛🦋🐌🐞🐜🪲🦂🐢🐍🦎🦖🦕🐙🪼🦐🦞🦀🐡🐠🐟🐬🐳🦈🦭🐊🦍🦧🐩🐓🦃🦤🦚🦜🦢🦩🐇🦝🦨🦡🦫🦦🦥🐁🐀🦔🐉"
)


def thread_emoji(thread_id: int | threading.Thread | None = None):
    """Cute little helper that assigns each thread a unique emoji."""
    if isinstance(thread_id, threading.Thread):
        thread_id = thread_id.ident

    is_main_thread = threading.current_thread() is threading.main_thread()

    if thread_id is None and is_main_thread or thread_id == threading.main_thread().ident:
        return "⭐️"

    if thread_id is None:
        thread_id = threading.get_ident()

    return _EMOJI[thread_id % len(_EMOJI)]
