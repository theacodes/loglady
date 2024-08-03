# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


import threading

from loglady.threading import thread_emoji


def test_main_thread_implied():
    emoji = thread_emoji()
    assert emoji == "⭐️"


def test_main_thread_explicit():
    thread = threading.main_thread()
    assert thread_emoji(thread) == "⭐️"
    assert thread_emoji(thread.ident) == "⭐️"


def test_other_thread_explicit():
    def thread_main():
        return

    thread = threading.Thread(target=thread_main)
    thread.start()

    assert thread_emoji(thread) != "⭐️"
    assert thread_emoji(thread.ident) != "⭐️"
