from contextlib import contextmanager
from threading import local

class AppContext:
    def __init__(self, app):
        self.app = app

    def push(self):
        _app_ctx_stack.top = self

    def pop(self):
        _app_ctx_stack.top = None

@contextmanager
def app_context(app):
    ctx = AppContext(app)
    ctx.push()
    try:
        yield
    finally:
        ctx.pop()

class LocalStack:
    def __init__(self):
        self._local = local()

    @property
    def top(self):
        return getattr(self._local, 'top', None)

    @top.setter
    def top(self, value):
        self._local.top = value

_app_ctx_stack = LocalStack()

def current_app():
    return _app_ctx_stack.top.app

def g():
    return current_app().g
