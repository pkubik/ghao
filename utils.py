import logging


log = logging.getLogger(__name__)


def action_handler(fn):
    def handler(_action, _params):
        return fn()
    return handler


def debug_action_handler(fn):
    def handler(action, params):
        log.info(f"{action}({params})")
        return fn()
    return handler
