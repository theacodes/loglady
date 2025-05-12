# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import pytest

import loglady


@pytest.fixture
def log_before_after():
    loglady.warning("fixture before")
    yield
    loglady.warning("fixture after")


def test_passing(log_before_after):
    loglady.info("within test")


def test_failing(log_before_after):
    loglady.info("within test")
    assert False, "This test is failing on purpose"  # noqa: B011, PT015


@pytest.fixture
def fixture_fails_during_setup():
    loglady.warning("fixture before")
    raise ValueError("This fixture fails during setup")  # noqa: EM101, TRY003


def test_fails_during_setup(fixture_fails_during_setup):
    assert False, "should not execute this test"  # noqa: B011, PT015


@pytest.fixture
def fixture_fails_during_teardown():
    loglady.warning("fixture before")
    yield
    loglady.warning("fixture after before raise")
    raise ValueError("This fixture fails during teardown")  # noqa: EM101, TRY003


def test_fails_during_teardown(fixture_fails_during_teardown):
    loglady.info("within test")
