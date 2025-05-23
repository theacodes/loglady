# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT


from typing import Any


class LogladyWarning(UserWarning):
    pass


class NotConfiguredWarning(LogladyWarning):
    """Warning for when loglady is not configured and fallback mode is set to 'warn'."""

    def __init__(self) -> None:
        super().__init__("log() called before loglady.configure() and no fallback available.")


class BackgroundThreadWarning(LogladyWarning):
    """Warning for when the background thread is stopped with an unexpected exception."""

    def __init__(self, *, error: Exception) -> None:
        super().__init__(f"background thread shutdown due to unexpected error: {error!r}")


class UndeliveredLogsWarning(LogladyWarning):
    """Warning for when the background thread transport is stopped but there are still undelivered logs."""

    def __init__(self, *, remaining_logs: int) -> None:
        super().__init__(f"background thread shutdown with {remaining_logs} logs undelivered.")


class DestinationErrorWarning(LogladyWarning):
    """Warning for when a destination raises an error in the background thread."""

    def __init__(self, *, destination: Any, error: Exception) -> None:
        super().__init__(f"error in background thread while delivering log to destination {destination!r}: {error!r}")
