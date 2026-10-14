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
            ctx = self.__local.top
            if ctx is None:
                raise RuntimeError(f'Working outside of application context')
            return getattr(ctx, self.__name)
        except AttributeError:
            raise RuntimeError(f'Working outside of application context')
    
    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)
    
    def __setattr__(self, name, value):
        setattr(self._get_current_object(), name, value)
    
    def __delattr__(self, name):
        delattr(self._get_current_object(), name)


class AppContext:
    """Application context that holds app-specific data."""
    
    def __init__(self, app):
        self.app = app
        self.g = G()
    
    def __enter__(self):
        _app_ctx_stack.push(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _app_ctx_stack.pop()


class G:
    """A namespace object that can store data during an application context."""
    pass


class LocalStack:
    """A thread-local stack."""
    
    def __init__(self):
        self._local = threading.local()
    
    def push(self, obj):
        stack = getattr(self._local, 'stack', None)
        if stack is None:
            self._local.stack = stack = []
        stack.append(obj)
    
    def pop(self):
        stack = getattr(self._local, 'stack', None)
        if stack is None or not stack:
            return None
        return stack.pop()
    
    @property
    def top(self):
        stack = getattr(self._local, 'stack', None)
        if stack is None or not stack:
            return None
        return stack[-1]


# Global context stacks
_app_ctx_stack = LocalStack()

# Proxies that provide access to current app and g
current_app = LocalProxy(_app_ctx_stack, 'app')
g = LocalProxy(_app_ctx_stack, 'g')
