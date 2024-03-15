# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import threading

_ANIMALS = list(
    "🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐽🐸🐵🐔🐧🐦🐤🪿🦆🦉🦇🦇🐺🐗🐴🦄🫎🐝🪱🐛🦋🐌🐞🐜🪰🪲🪳🦟🦗🕷️🕸️🦂🐢🐍🦎🦖🦕🐙🦑🪼🦐🦞🦀🐡🐠🐟🐬🐳🐋🦈🦭🐊🐅🐆🦓🦍🦧🦣🐘🦛🦏🐪🐫🦒🦘🦬🐃🐂🐄🫏🐎🐖🐏🐑🦙🐐🦌🐕🐩🐈🐓🦃🦤🦚🦜🦢🦩🕊️🐇🦝🦨🦡🦫🦦🦥🐁🐀🐿️🦔🐉🐲"
)


def thread_emoji(thread_id=None):
    """Cute little helper that assigns each thread a unique emoji."""
    is_main_thread = threading.current_thread() is threading.main_thread()

    if thread_id is None and is_main_thread or thread_id == threading.main_thread().native_id:
        return "⭐️"

    if thread_id is None:
        thread_id = threading.get_native_id()

    return _ANIMALS[thread_id % len(_ANIMALS)]
