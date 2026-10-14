"""
Application context management using thread-local storage.
"""

import threading
from typing import Any, Optional


class LocalProxy:
    """A proxy object that forwards operations to a thread-local object."""
    
    def __init__(self, local_func):
        self._local_func = local_func
    
    def __getattr__(self, name):
        return getattr(self._local_func(), name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._local_func(), name, value)


class AppContext:
    """Application context that holds app-specific data."""
    
    def __init__(self, app):
        self.app = app
        self.g = SimpleNamespace()
    
    def __enter__(self):
        _app_ctx_stack.push(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _app_ctx_stack.pop()


class SimpleNamespace:
    """Simple object for storing arbitrary attributes."""
    pass


class LocalStack:
    """A thread-local stack."""
    
    def __init__(self):
        self._local = threading.local()
    
    def push(self, obj):
        if not hasattr(self._local, 'stack'):
            self._local.stack = []
        self._local.stack.append(obj)
    
    def pop(self):
        if hasattr(self._local, 'stack') and self._local.stack:
            return self._local.stack.pop()
        return None
    
    @property
    def top(self):
        if hasattr(self._local, 'stack') and self._local.stack:
            return self._local.stack[-1]
        return None


# Global context stacks
_app_ctx_stack = LocalStack()


def _get_current_app():
    """Get the current application from the context stack."""
    ctx = _app_ctx_stack.top
    if ctx is None:
        raise RuntimeError("Working outside of application context")
    return ctx.app


def _get_g():
    """Get the current g object from the context stack."""
    ctx = _app_ctx_stack.top
    if ctx is None:
        raise RuntimeError("Working outside of application context")
    return ctx.g


# Proxy objects for accessing current app and g
current_app = LocalProxy(_get_current_app)
g = LocalProxy(_get_g)
