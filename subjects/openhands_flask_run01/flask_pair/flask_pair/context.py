
from threading import local

class AppContext:
    def __init__(self):
        self._storage = local()

    def __enter__(self):
        self._storage.current_app = None
        self._storage.g = {}

    def __exit__(self, exc_type, exc_value, traceback):
        self._storage.current_app = None
        self._storage.g = None

current_app = None
g = {}