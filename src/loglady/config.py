# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Global configuration for LogLady.

This global config is used by magics (the top-level loglady.info, etc.), and
should be configured at application startup.
"""

from . import manager_stack
from ._excepthook import install_excepthook, is_repl
from .destination import DestinationList
from .manager import Manager
from .middleware import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp, fancy_prefix_icon
from .rich import RichConsoleDestination
from .transport import SyncTransport, ThreadedTransport, Transport
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
    if once and manager_stack.has_valid_manager():
        return manager_stack.current()

    if transport is None:
        if is_repl():
            transport = SyncTransport()
        else:
            transport = ThreadedTransport()

    if destinations is None:
        destinations = [RichConsoleDestination()]

    mgr = Manager(
        transport=transport,
        middleware=middleware,
        destinations=destinations,
    )
    mgr.start()

    manager_stack.push(mgr)

    if not is_repl() and install_hook:
        install_excepthook()

    return mgr
