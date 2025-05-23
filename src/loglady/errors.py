# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from collections.abc import Sequence


class LogladyError(Exception):
    """Base class for all LogLady errors."""


class InvalidFallbackModeError(LogladyError):
    """Raised when an invalid fallback mode is specified."""

    def __init__(self, *, mode: str, valid_options: Sequence[str]) -> None:
        super().__init__(f'fallback mode must be one of {",".join(valid_options)}, got "{mode}"')


class NotConfiguredError(RuntimeError):
    """Raised when loglady is not configured and fallback mode is set to 'error'."""

    def __init__(self) -> None:
        super().__init__("log() called before loglady.configure() and no fallback available.")
