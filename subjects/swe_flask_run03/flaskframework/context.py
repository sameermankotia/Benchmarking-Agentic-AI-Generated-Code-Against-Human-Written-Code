"""
Application context management using thread-local storage.
"""
import threading
from typing import Any


class LocalProxy:
    """A proxy object that forwards all operations to a thread-local object."""
    
    def __init__(self, local, name):
        object.__setattr__(self, '_local', local)
        object.__setattr__(self, '_name', name)
    
    def _get_current_object(self):
        """Get the current object from thread-local storage."""
        try:
            return getattr(self._local, self._name)
        except AttributeError:
            raise RuntimeError(f'Working outside of application context')
    
    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)
    
    def __setattr__(self, name, value):
        setattr(self._get_current_object(), name, value)
    
    def __delattr__(self, name):
        delattr(self._get_current_object(), name)


class AppContext:
    """Application context that holds app and g objects."""
    
    def __init__(self, app):
        self.app = app
        self.g = G()


class G:
    """A simple object to store data during a request."""
    pass


class LocalStack:
    """A thread-local stack for managing contexts."""
    
    def __init__(self):
        self._local = threading.local()
    
    def push(self, obj):
        """Push an object onto the stack."""
        if not hasattr(self._local, 'stack'):
            self._local.stack = []
        self._local.stack.append(obj)
    
    def pop(self):
        """Pop an object from the stack."""
        if not hasattr(self._local, 'stack') or not self._local.stack:
            return None
        return self._local.stack.pop()
    
    @property
    def top(self):
        """Get the top object from the stack."""
        if not hasattr(self._local, 'stack') or not self._local.stack:
            return None
        return self._local.stack[-1]


# Global context stack
_app_ctx_stack = LocalStack()

# Create a custom proxy for current_app and g
class _AppProxy(LocalProxy):
    def _get_current_object(self):
        ctx = _app_ctx_stack.top
        if ctx is None:
            raise RuntimeError('Working outside of application context')
        return ctx.app

class _GProxy(LocalProxy):
    def _get_current_object(self):
        ctx = _app_ctx_stack.top
        if ctx is None:
            raise RuntimeError('Working outside of application context')
        return ctx.g

# Proxy objects for current_app and g
current_app = _AppProxy(_app_ctx_stack, 'top')
g = _GProxy(_app_ctx_stack, 'top')
