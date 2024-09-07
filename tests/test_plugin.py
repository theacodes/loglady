# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import loglady

from .utils import assert_dict_subset


def test_capture(loglady_capture):
    loglady.info("Hello!")
    assert len(loglady_capture) == 1
    assert_dict_subset(loglady_capture[0], dict(msg="Hello!"))


def test_stdout(capsys):
    loglady.info("Hello!")
    captured = capsys.readouterr()
    # Loglady should *not* be writing to stdout be default during tests
    assert "Hello!" not in captured.out
