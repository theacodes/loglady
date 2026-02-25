# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import loglady


def test_capture(loglady_capture):
    loglady.info("Hello!")
    assert len(loglady_capture) == 1
    assert loglady_capture[0] == loglady.CompareRecord(message="Hello!")


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


def test_show_logs(pytester):
    pytester.copy_example("tests/scripts/deferred_capture.py")

    result = pytester.runpytest("deferred_capture.py::test_passing", "--loglady-stdout", "-s")

    result.stdout.fnmatch_lines("plugins:*loglady-*.*.*")  # Loglady version should be in the output
    result.stdout.fnmatch_lines("*1 passed*")  # should run one test and pass
    result.stdout.no_fnmatch_line("*Captured [*]loglady[*]*")  # should not print captured logs here
    result.stdout.fnmatch_lines("*within test*")  # should have printed the logs as they came in
