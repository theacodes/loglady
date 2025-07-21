# Copyright (c) 2025 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

from loglady.exception_capture import capture_exception


class CustomError(Exception):
    pass


def test_capture_exception_without_traceback():
    result = capture_exception(ValueError())
    assert result.type == "ValueError"
    assert result.module == "builtins"
    assert result.str == ""
    assert result.notes is None
    assert result.stack is None
    assert result.cause is None
    assert result.context is None
    assert result.exceptions is None

    result = capture_exception(ValueError("test error"))
    assert result.type == "ValueError"
    assert result.module == "builtins"
    assert result.str == "test error"

    result = capture_exception(ValueError("test error", 1, 2, 3))
    assert result.type == "ValueError"
    assert result.module == "builtins"
    assert result.str == "('test error', 1, 2, 3)"

    result = capture_exception(CustomError("custom error"))
    assert result.type == "CustomError"
    assert result.module == __name__
    assert result.str == "custom error"


def test_capture_exception_with_traceback():
    # Use a thrown exception to generate a traceback.
    def make_exception(*args) -> ValueError:
        try:
            raise ValueError(*args)  # noqa: TRY301
        except ValueError as e:
            return e

    exc = make_exception("test error", 1, 2, 3)
    result = capture_exception(exc)

    assert result.stack is not None
    frame = result.stack[-1]

    assert frame.filename == __file__
    assert frame.name == "make_exception"


def test_capture_exception_with_notes():
    err = ValueError()
    err.add_note("Note 1")
    err.add_note("Note 2")
    assert capture_exception(err).notes == ("Note 1", "Note 2")


def test_capture_exception_with_context():
    # context is the exception that was being processed when the exception was raised, and it only set when not
    # using `raise from` syntax.

    def make_exception(*args):
        try:
            try:
                _ = 10 / 0
            except ZeroDivisionError:
                raise ValueError(*args)  # noqa: B904
        except ValueError as e:
            return e
        raise RuntimeError("This should never happen")  # noqa: EM101, TRY003

    err = make_exception("test error", 1, 2, 3)
    result = capture_exception(err)

    assert result.type == "ValueError"
    assert result.context is not None
    assert result.context.type == "ZeroDivisionError"
    assert result.context.module == "builtins"
    assert result.context.str == "division by zero"

    assert result.cause is None


def test_capture_exception_with_cause():
    # cause is the exception specified by the `raise from` syntax
    def make_exception(*args):
        try:
            try:
                _ = 10 / 0
            except ZeroDivisionError as e:
                raise ValueError(*args) from e
        except ValueError as e:
            return e
        raise RuntimeError("This should never happen")  # noqa: EM101, TRY003

    err = make_exception("test error", 1, 2, 3)
    result = capture_exception(err)

    assert result.type == "ValueError"
    assert result.cause is not None
    assert result.cause.type == "ZeroDivisionError"
    assert result.cause.module == "builtins"
    assert result.cause.str == "division by zero"

    assert result.context is None


def test_capture_exception_group():
    exc_group = ExceptionGroup("Multiple errors", [ValueError("oops"), KeyError("my bad")])

    result = capture_exception(exc_group)

    assert result.type == "ExceptionGroup"
    assert result.module == "builtins"
    assert result.str == "Multiple errors (2 sub-exceptions)"

    assert result.exceptions is not None
    assert len(result.exceptions) == 2
    assert result.exceptions[0].type == "ValueError"
    assert result.exceptions[0].str == "oops"
    assert result.exceptions[1].type == "KeyError"
    assert result.exceptions[1].str == "'my bad'"
