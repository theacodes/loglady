# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Global configuration for LogLady.

This global config is used by magics (the top-level loglady.info, etc.), and
should be configured at application startup.
"""

import sys

from . import _config_stack
from .destination import DestinationList
from .manager import Manager
from .middleware import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp, fancy_prefix_icon
from .rich import RichConsoleDestination
from .transport import ThreadedTransport, Transport
from .types import MiddlewareList

DEFAULT_MIDDLEWARE = (
    add_timestamp,
    add_thread_info,
    add_exception_and_stack_info,
    add_call_info,
    fancy_prefix_icon,
)


def configure(
    *,
    transport: Transport | None = None,
    middleware: MiddlewareList = DEFAULT_MIDDLEWARE,
    destinations: DestinationList | None = None,
    once: bool = False,
    install_hook: bool = True,
) -> Manager:
    """Configure LogLady.

    This creates global configuration for LogLady that's then available via the
    top-level loglady.info(...), loglady.logger(...), etc. methods (these are
    called "magics").

    This creates a Manager instance and start()s it so that any background
    stuff can happen. It also installs an atexit() handler to call the Manager's
    stop() to ensure all logs are written before exit.
    """
    if once and _config_stack.top():
        return manager()

    if transport is None:
        transport = ThreadedTransport()

    if destinations is None:
        destinations = [RichConsoleDestination()]

    mgr = Manager(
        transport=transport,
        middleware=middleware,
        destinations=destinations,
    )
    mgr.start()

    _config_stack.push(_config_stack.GlobalState(mgr))

    if install_hook and sys.excepthook == sys.__excepthook__:
        sys.excepthook = _excepthook

    return mgr


def manager() -> Manager:
    """Returns the currently configured Manager, or None if not configured."""
    state = _config_stack.top()
    if state is None:
        msg = "LogLady has not been configured!"
        raise RuntimeError(msg)
    return state.manager


def _excepthook(exc_type, value, traceback):
    state = _config_stack.top()
    if state is None:
        sys.__excepthook__(exc_type, value, traceback)
        return

    state.manager.flush()

    state.manager.logger().log(
        "unhandled exception, sys.excepthook() called",
        level="error",
        exception=(
            exc_type,
            value,
            traceback,
        ),
    )

    state.manager.flush()
    state.manager.stop()
