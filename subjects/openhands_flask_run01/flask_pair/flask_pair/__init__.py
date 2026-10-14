
from .request import Request
from .response import Response
from .routing import Router
from .context import AppContext, current_app, g
from .blueprints import Blueprint

class FlaskPair:
    def __init__(self):
        self.router = Router()
        self.context = AppContext()

    def route(self, path, methods=None):
        def decorator(func):
            self.router.add_route(path, func, methods)
            return func
        return decorator

    def wsgi_app(self, environ, start_response):
        with self.context:
            request = Request(environ)
            response = self.router.dispatch(request)
            start_response(response.status, response.headers)
            return [response.body.encode()]

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def run(self, host="127.0.0.1", port=5000):
        from werkzeug.serving import run_simple
        run_simple(host, port, self)