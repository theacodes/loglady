# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Global configuration for LogLady.

This global config is used by magics (the top-level loglady.info, etc.), and
should be configured at application startup.
"""

import sys
from collections.abc import Sequence

from . import manager_stack, processors
from .destinations import ReprFormatter, TextIODestination
from .excepthook import install_excepthook, is_repl
from .manager import Manager
from .processor import Processor
from .rich import RichConsoleDestination
from .thread_transport import ThreadTransport

DEFAULT_PROCESSORS = (
    processors.add_timestamp,
    processors.add_thread_info,
    processors.add_call_info,
    processors.fancy_prefix_icon,
    processors.eagerly_capture_exceptions,
)


def configure(
    *,
    threaded: bool | None = None,
    rich: bool = True,
    once: bool = False,
    excepthook: bool = True,
    processors: Sequence[Processor] | None = None,
) -> Manager:
    """Configure LogLady.

    This creates global configuration for LogLady that's then available via the
    top-level loglady.info(...), loglady.logger(...), etc. methods (these are
    called "magics").

    This creates a Manager instance and start()s it so that any background
    stuff can happen. It also installs an atexit() handler to call the Manager's
    stop() to ensure all logs are written before exit.
    """
    if (mgr := _check_once(once)) is not None:
        return mgr

    processors = [*DEFAULT_PROCESSORS, *(processors or ())]

    if rich:
        destination = RichConsoleDestination()
    else:
        destination = TextIODestination(io=sys.stderr, formatter=ReprFormatter())

    if threaded is None:
        threaded = not is_repl()

    if threaded:
        transport = ThreadTransport([destination])
        transport.start()
        processors.append(transport)
    else:
        processors.append(destination)

    if excepthook:
        _setup_excepthook()

    return create_manager(processors)


def create_manager(processors: Sequence[Processor]):
    mgr = Manager(processors=list(processors))
    manager_stack.push(mgr)
    return mgr


def _check_once(once: bool) -> Manager | None:  # noqa: FBT001
    if not once:
        return None
    if manager_stack.has_valid_manager():
        manager_stack.current()
    return None


def _setup_excepthook(install: bool = True):  # noqa: FBT001, FBT002
    if install and not is_repl():
        install_excepthook()
