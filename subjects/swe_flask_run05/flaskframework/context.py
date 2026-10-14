"""
Application context management using thread-local storage.
"""
import threading
from typing import Any


class LocalProxy:
    """A proxy to a thread-local object."""
    
    def __init__(self, local, name):
        object.__setattr__(self, '_LocalProxy__local', local)
        object.__setattr__(self, '_LocalProxy__name', name)
    
    def _get_current_object(self):
        try:
            return getattr(self.__local, self.__name)
        except AttributeError:
            raise RuntimeError(f'Working outside of application context')
    
    def __getattr__(self, name):
        return getattr(self._get_current_object(), name)
    
    def __setattr__(self, name, value):
        setattr(self._get_current_object(), name, value)
    
    def __delattr__(self, name):
        delattr(self._get_current_object(), name)
    
    def __eq__(self, other):
        return self._get_current_object() == other
    
    def __ne__(self, other):
        return not self.__eq__(other)


class Local:
    """Thread-local storage."""
    
    def __init__(self):
        object.__setattr__(self, '_storage', threading.local())
    
    def __getattr__(self, name):
        try:
            return getattr(self._storage, name)
        except AttributeError:
            raise AttributeError(name)
    
    def __setattr__(self, name, value):
        setattr(self._storage, name, value)
    
    def __delattr__(self, name):
        delattr(self._storage, name)


class AppContext:
    """Application context."""
    
    def __init__(self, app):
        self.app = app
        self.g = SimpleNamespace()
    
    def __enter__(self):
        _app_ctx_stack.app = self.app
        _app_ctx_stack.g = self.g
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            delattr(_app_ctx_stack, 'app')
        except AttributeError:
            pass
        try:
            delattr(_app_ctx_stack, 'g')
        except AttributeError:
            pass


class SimpleNamespace:
    """Simple object for storing arbitrary attributes."""
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# Global thread-local storage
_app_ctx_stack = Local()

# Proxies for current_app and g
current_app = LocalProxy(_app_ctx_stack, 'app')
g = LocalProxy(_app_ctx_stack, 'g')
