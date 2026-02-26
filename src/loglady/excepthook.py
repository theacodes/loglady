# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import sys
from types import TracebackType

from . import manager_stack


def install_excepthook():
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = excepthook


def excepthook(
    exc_type: type[BaseException],
    value: BaseException,
    traceback: TracebackType | None,
):
    if not manager_stack.has_valid_manager():
        sys.__excepthook__(exc_type, value, traceback)
        return

    try:
        manager_stack.flush_all()

        manager_stack.logger().exception(
            "Unhandled exception, sys.excepthook() called",
            value,
        )

        manager_stack.flush_all()
        manager_stack.stop_all()

    except Exception as err:  # noqa: BLE001
        # If something goes wrong in our excepthook, defer to the default one and log a short message.
        print(
            f"An error occurred in loglady's excepthook, falling back to the default excepthook. Error: {err!r}",
            file=sys.stderr,
        )
        sys.__excepthook__(exc_type, value, traceback)
