import threading
from jinja2 import Environment, FileSystemLoader
from wsgiref.simple_server import make_server
from .request import Request
from .response import Response

class FlaskApp:
    def __init__(self, import_name):
        self.import_name = import_name
        self.routes = {}
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        self.app_context = threading.local()

    def route(self, path, methods=None):
        if methods is None:
            methods = ['GET']

        def decorator(func):
            self.routes[(path, tuple(methods))] = func
            return func

        return decorator

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.handle_request(request)
        start_response(response.status, response.headers)
        return [response.body.encode()]

    def handle_request(self, request):
        handler = self.routes.get((request.path, tuple([request.method])))
        if handler is None:
            return Response('Not Found', status=404)
        return handler(request)

    def run(self, host='127.0.0.1', port=5000):
        with make_server(host, port, self) as server:
            print(f"Running on http://{host}:{port}/ (Press CTRL+C to quit)")
            server.serve_forever()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)