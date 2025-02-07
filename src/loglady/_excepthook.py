# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import sys

from . import manager_stack


def is_repl() -> bool:
    return hasattr(sys, "ps1")


def install_excepthook():
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = _excepthook


def _excepthook(exc_type, value, traceback):
    if not manager_stack.has_valid_manager():
        sys.__excepthook__(exc_type, value, traceback)
        return

    manager_stack.flush_all()

    manager_stack.logger().log(
        "unhandled exception, sys.excepthook() called",
        level="error",
        exception=(
            exc_type,
            value,
            traceback,
        ),
    )

    manager_stack.flush_all()
    manager_stack.stop_all()
