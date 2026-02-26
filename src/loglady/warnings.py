# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


class LogladyWarning(UserWarning):
    pass


class NotConfiguredWarning(LogladyWarning):
    """Warning for when loglady is not configured and fallback mode is set to 'warn'."""

    def __init__(self) -> None:
        super().__init__("log() called before loglady.configure() and no fallback available.")
