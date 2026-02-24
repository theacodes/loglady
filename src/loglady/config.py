# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Global configuration for LogLady.

This global config is used by magics (the top-level loglady.info, etc.), and
should be configured at application startup.
"""

from . import manager_stack, processors
from .destination import DestinationList
from .excepthook import install_excepthook, is_repl
from .manager import Manager
from .rich import RichConsoleDestination
from .transport import SyncTransport, ThreadedTransport, Transport
from .types import ProcessorList

DEFAULT_PROCESSORS = (
    processors.add_timestamp,
    processors.add_thread_info,
    processors.add_call_info,
    processors.fancy_prefix_icon,
    processors.eagerly_capture_exceptions,
)


def configure(
    *,
    transport: Transport | None = None,
    processors: ProcessorList = DEFAULT_PROCESSORS,
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
            transport.start()

    if destinations is None:
        destinations = [RichConsoleDestination()]

    if not transport.destinations:
        transport.destinations = destinations

    mgr = Manager(
        transport=transport,
        processors=processors,
    )

    manager_stack.push(mgr)

    if not is_repl() and install_hook:
        install_excepthook()

    return mgr
