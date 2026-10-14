"""
Application context management using thread-local storage.
"""

import threading
from typing import Any, Optional


class LocalProxy:
    """A proxy to a thread-local object."""
    
    def __init__(self, local, name):
        object.__setattr__(self, '_LocalProxy__local', local)
        object.__setattr__(self, '_LocalProxy__name', name)
    
    def _get_current_object(self):
        try:
            # Get the top of the stack and then the attribute
            top = self.__local.top
            if top is None:
                raise AttributeError('No context')
            return getattr(top, self.__name)
        except AttributeError:
            raise RuntimeError(f'Working outside of application context')
    
    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)
    
    def __setattr__(self, name, value):
        setattr(self._get_current_object(), name, value)


class LocalStack:
    """A thread-local stack."""
    
    def __init__(self):
        self._local = threading.local()
    
    def push(self, obj):
        rv = getattr(self._local, 'stack', None)
        if rv is None:
            self._local.stack = rv = []
        rv.append(obj)
        return rv
    
    def pop(self):
        stack = getattr(self._local, 'stack', None)
        if stack is None:
            return None
        elif len(stack) == 1:
            return stack[-1]
        else:
            return stack.pop()
    
    @property
    def top(self):
        try:
            return self._local.stack[-1]
        except (AttributeError, IndexError):
            return None


class AppContext:
    """Application context."""
    
    def __init__(self, app):
        self.app = app
        self.g = SimpleNamespace()
    
    def push(self):
        _app_ctx_stack.push(self)
    
    def pop(self):
        return _app_ctx_stack.pop()
    
    def __enter__(self):
        self.push()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pop()


class SimpleNamespace:
    """Simple object for storing arbitrary attributes."""
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# Global context stacks
_app_ctx_stack = LocalStack()

# Proxies for accessing current context
current_app = LocalProxy(_app_ctx_stack, 'app')
g = LocalProxy(_app_ctx_stack, 'g')
