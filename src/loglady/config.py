# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import atexit

from .manager import Manager
from .middleware import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp
from .rich import RichConsoleDestination
from .transport import ThreadedTransport, Transport
from .types import DestinationList, MiddlewareList


class _GlobalConfig:
    is_configured: bool = False
    manager: Manager | None = None


_CONFIG = _GlobalConfig()

DEFAULT_MIDDLEWARE = (
    add_timestamp,
    add_thread_info,
    add_exception_and_stack_info,
    add_call_info,
)


def configure(
    *,
    transport: Transport | None = None,
    middleware: MiddlewareList = DEFAULT_MIDDLEWARE,
    destinations: DestinationList | None = None,
    replace: bool = False,
):
    if not replace and _CONFIG.is_configured:
        msg = "LogLady has already been configured"
        raise RuntimeError(msg)
    _CONFIG.is_configured = True

    if transport is None:
        transport = ThreadedTransport()

    if destinations is None:
        destinations = [RichConsoleDestination()]

    if _CONFIG.manager is not None:
        _CONFIG.manager.stop()

    _CONFIG.manager = Manager(
        transport=transport,
        middleware=middleware,
        destinations=destinations,
    )
    _CONFIG.manager.start()

    return _CONFIG.manager


def manager():
    """Get the currently configured log manager"""
    if not _CONFIG.is_configured or _CONFIG.manager is None:
        msg = "LogLady has not been configured!"
        raise RuntimeError(msg)
    return _CONFIG.manager


def _shutdown_loglady():
    if _CONFIG.manager is None:
        return

    _CONFIG.manager.stop()


_ = atexit.register(_shutdown_loglady)
