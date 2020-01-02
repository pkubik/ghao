import logging
import threading
import plumbum as pb

from ghao.errors import GhaoRuntimeError

log = logging.getLogger(__name__)


def action_handler(fn):
    def handler(_action, _params):
        return fn()
    return handler


def threaded_action_handler(fn):
    """
    Note: It doesn't return the value of the function. Just fire and forget.
    """
    def handler(_action, _params):
        threading.Thread(target=fn, daemon=True).start()
    return handler


def debug_action_handler(fn):
    def handler(action, params):
        log.info(f"{action}({params})")
        return fn()
    return handler


def get_command_base(name: str):
    try:
        cmd = pb.local[name]
        return cmd
    except pb.CommandNotFound as e:
        log.error(f"{e.program} was not found.\n"
                  "Make sure that it's installed before using this tool.")
        raise GhaoRuntimeError(f"Command `{name}` not found.")
