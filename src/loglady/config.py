# Copyright (c) 2024 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import atexit

from . import _config_stack
from .destination import DestinationList
from .manager import Manager
from .middleware import add_call_info, add_exception_and_stack_info, add_thread_info, add_timestamp
from .rich import RichConsoleDestination
from .transport import ThreadedTransport, Transport
from .types import MiddlewareList

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
    once: bool = False,
):
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

    return mgr


def manager() -> Manager:
    """Get the currently configured log manager"""
    state = _config_stack.top()
    if state is None:
        msg = "LogLady has not been configured!"
        raise RuntimeError(msg)
    return state.manager


def _shutdown_loglady():
    while state := _config_stack.pop():
        state.manager.stop()


_ = atexit.register(_shutdown_loglady)
