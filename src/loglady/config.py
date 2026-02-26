# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

"""Global configuration for LogLady.

This global config is used by magics (the top-level loglady.info, etc.), and
should be configured at application startup.
"""

import os
import sys
from collections.abc import Sequence

from . import manager_stack, processors
from .destinations import ReprFormatter, TextIODestination
from .excepthook import install_excepthook
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
    excepthook: bool | None = None,
    processors: Sequence[Processor] | None = None,
) -> Manager:
    """Configure LogLady.

    This creates global configuration for LogLady that's then available via the top-level `loglady.info(...)`,
    `loglady.logger(...)`, etc. methods (these are called "magics").

    Args:
    - threaded: Whether to use a background thread to write logs. Defaults to True unless we're in a REPL or in tests,
      in which case it defaults to False.
    - rich: Whether to use Rich to write logs. Defaults to True.
    - once: If True, this will only configure LogLady if it hasn't already been configured.
    - excepthook: Whether to install an excepthook that logs uncaught exceptions. Defaults to True unless we're in a
      REPL or in tests.
    - processors: Additional processors to add after the default ones.

    """
    if (mgr := _check_once(once)) is not None:
        return mgr

    processors = [*DEFAULT_PROCESSORS, *(processors or ())]

    if rich:
        destination = RichConsoleDestination()
    else:
        destination = TextIODestination(io=sys.stderr, formatter=ReprFormatter())

    if threaded is None:
        threaded = not _is_repl() and not _is_pytest()

    if threaded:
        transport = ThreadTransport([destination])
        transport.start()
        processors.append(transport)
    else:
        processors.append(destination)

    if excepthook is None:
        excepthook = not _is_repl() and not _is_pytest()

    if excepthook:
        _setup_excepthook()

    return create_manager(processors)


def create_manager(processors: Sequence[Processor]):
    mgr = Manager(processors=list(processors))
    manager_stack.push(mgr)
    return mgr


def _is_repl() -> bool:
    return hasattr(sys, "ps1")


def _is_pytest() -> bool:
    return os.environ.get("PYTEST_VERSION") is not None


def _check_once(once: bool) -> Manager | None:  # noqa: FBT001
    if not once:
        return None
    if manager_stack.has_valid_manager():
        manager_stack.current()
    return None


def _setup_excepthook(install: bool = True):  # noqa: FBT001, FBT002
    if install and not _is_repl():
        install_excepthook()
