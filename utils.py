def action_handler(fn):
    def handler(_action, _params):
        return fn()
    return handler
