
import threading
from jinja2 import Environment, FileSystemLoader
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

class Request:
    def __init__(self, environ):
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO']
        self.headers = {key[5:].replace('_', '-').title(): value for key, value in environ.items() if key.startswith('HTTP_')}
        self.query = parse_qs(environ['QUERY_STRING'])
        try:
            self.body = environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', 0)))
        except (TypeError, ValueError):
            self.body = b''

class Response:
    def __init__(self, body='', status=200, headers=None):
        self.body = body.encode('utf-8') if isinstance(body, str) else body
        self.status = status
        self.headers = headers or {}

    def __call__(self, start_response):
        status_text = f"{self.status} OK" if self.status == 200 else f"{self.status} ERROR"
        start_response(status_text, list(self.headers.items()))
        return [self.body]

class FlaskPair:
    def __init__(self):
        self.routes = {}
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        self.app_context = threading.local()

    def route(self, path, methods=None):
        methods = methods or ['GET']
        def decorator(func):
            self.routes[(path, tuple(methods))] = func
            return func
        return decorator

    def __call__(self, environ, start_response):
        request = Request(environ)
        self.app_context.current_app = self
        handler = self.routes.get((request.path, (request.method,)))
        if handler:
            response = handler(request)
        else:
            response = Response('Not Found', status=404)
        return response(start_response)

    def run(self, host='127.0.0.1', port=5000):
        with make_server(host, port, self) as server:
            print(f"Running on http://{host}:{port}/")
            server.serve_forever()

    def render_template(self, template_name, **context):
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

current_app = None
g = threading.local()