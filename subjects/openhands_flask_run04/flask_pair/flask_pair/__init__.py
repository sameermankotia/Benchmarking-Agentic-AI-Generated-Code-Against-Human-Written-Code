from .routing import Router
from .request import Request
from .response import Response
from .context import AppContext, current_app, g
from .blueprints import Blueprint
from .server import run_dev_server

class Flask:
    def __init__(self, name):
        self.name = name
        self.router = Router()
        self.context = AppContext(self)

    def route(self, path, methods=['GET']):
        def decorator(func):
            self.router.add_route(path, func, methods)
            return func
        return decorator

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.router.dispatch(request)
        start_response(response.status, response.headers)
        return [response.body.encode()]

    def __call__(self, environ, start_response):
        with self.context:
            return self.wsgi_app(environ, start_response)

    def run(self, host='127.0.0.1', port=5000):
        run_dev_server(self, host, port)
