# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import subprocess
import sys


def test_default_fallback_mode():
    # Default fallback mode should be stderr
    result = subprocess.run(
        [sys.executable, "tests/scripts/log_before_configure.py"], capture_output=True, check=True, text=True
    )
    assert "notset: loglady.log() before" in result.stderr
    assert "notset: logger.log() before" in result.stderr
    assert "█ loglady.log() after" in result.stdout
    assert "█ logger.log() after" in result.stdout


def test_fallback_stderr():
    result = subprocess.run(
        [sys.executable, "tests/scripts/log_before_configure.py"],
        capture_output=True,
        check=True,
        text=True,
        env=dict(LOGLADY_FALLBACK_MODE="stderr"),
    )
    assert "notset: loglady.log() before" in result.stderr
    assert "notset: logger.log() before" in result.stderr
    assert "█ loglady.log() after" in result.stdout
    assert "█ logger.log() after" in result.stdout


def test_fallback_buffer():
    result = subprocess.run(
        [sys.executable, "tests/scripts/log_before_configure.py"],
        capture_output=True,
        check=True,
        text=True,
        env=dict(LOGLADY_FALLBACK_MODE="buffer"),
    )
    assert "█ loglady.log() before" in result.stdout
    assert "█ logger.log() before" in result.stdout
    assert "█ loglady.log() after" in result.stdout
    assert "█ logger.log() after" in result.stdout


def test_fallback_warn():
    result = subprocess.run(
        [sys.executable, "tests/scripts/log_before_configure.py"],
        capture_output=True,
        check=True,
        text=True,
        env=dict(LOGLADY_FALLBACK_MODE="warn"),
    )
    assert "NotConfiguredWarning" in result.stderr
    assert "notset: loglady.log() before" in result.stderr
    assert "notset: logger.log() before" in result.stderr
    assert "█ loglady.log() after" in result.stdout
    assert "█ logger.log() after" in result.stdout


def test_fallback_error():
    result = subprocess.run(
        [sys.executable, "tests/scripts/log_before_configure.py"],
        capture_output=True,
        check=False,
        text=True,
        env=dict(LOGLADY_FALLBACK_MODE="error"),
    )
    assert "NotConfiguredError" in result.stderr


def test_buffer_and_exit_without_configure():
    result = subprocess.run(
        [sys.executable, "tests/scripts/log_without_configure.py"],
        capture_output=True,
        check=True,
        text=True,
        env=dict(LOGLADY_FALLBACK_MODE="buffer"),
    )
    assert "NotConfiguredWarning" in result.stderr
