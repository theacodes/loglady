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
    captured = capsys.readouterr()
    # Loglady should *not* be writing to stdout be default during tests
    assert "Hello!" not in captured.out


def test_capture_does_not_show_when_success(pytester):
    pytester.copy_example("tests/scripts/deferred_capture.py")

    result = pytester.runpytest("deferred_capture.py::test_passing")

    result.stdout.fnmatch_lines("plugins:*loglady-*.*.*")  # Loglady version should be in the output
    result.stdout.fnmatch_lines("*1 passed*")  # should run one test and pass
    result.stdout.no_fnmatch_line("*Captured [*]loglady[*]*")


def test_capture_renders_on_failure(pytester):
    pytester.copy_example("tests/scripts/deferred_capture.py")

    result = pytester.runpytest("deferred_capture.py::test_failing")

    result.stdout.fnmatch_lines("plugins:*loglady-*.*.*")  # Loglady version should be in the output
    result.stdout.fnmatch_lines("*1 failed*")  # should run one test and fail
    result.stdout.fnmatch_lines(["*Captured [*]loglady[*] setup*", "*fixture before*"])
    result.stdout.fnmatch_lines(["*Captured [*]loglady[*] call*", "*within test*"])
    result.stdout.fnmatch_lines(["*Captured [*]loglady[*] teardown*", "*fixture after*"])


def test_capture_renders_on_setup_failure(pytester):
    pytester.copy_example("tests/scripts/deferred_capture.py")

    result = pytester.runpytest("deferred_capture.py::test_fails_during_setup")

    result.stdout.fnmatch_lines("plugins:*loglady-*.*.*")  # Loglady version should be in the output
    result.stdout.fnmatch_lines("*1 error*")  # should fail during setup
    result.stdout.fnmatch_lines(["*[*]loglady[*] setup*", "*fixture before*"])


def test_capture_renders_on_teardown_failure(pytester):
    pytester.copy_example("tests/scripts/deferred_capture.py")

    result = pytester.runpytest("deferred_capture.py::test_fails_during_teardown")

    result.stdout.fnmatch_lines("plugins:*loglady-*.*.*")  # Loglady version should be in the output
    result.stdout.fnmatch_lines("*1 error*")  # should fail during setup
    result.stdout.fnmatch_lines(["*Captured [*]loglady[*] setup*", "*fixture before*"])
    result.stdout.fnmatch_lines(["*Captured [*]loglady[*] call*", "*within test*"])
    result.stdout.fnmatch_lines(["*Captured [*]loglady[*] teardown*", "*fixture after before raise*"])
