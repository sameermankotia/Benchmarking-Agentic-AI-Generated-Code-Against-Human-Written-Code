from wsgiref.simple_server import make_server
from jinja2 import Environment, FileSystemLoader
from threading import local
import re

class FlaskPair:
    def __init__(self):
        self.routes = []
        self.templates_env = Environment(loader=FileSystemLoader("templates"))
        self.context = local()

    def route(self, path, methods=None):
        def decorator(func):
            self.routes.append((path, methods, func))
            return func
        return decorator

    def wsgi_app(self, environ, start_response):
        path = environ['PATH_INFO']
        method = environ['REQUEST_METHOD']
        for route, methods, func in self.routes:
            match = re.fullmatch(route, path)
            if match and (methods is None or method in methods):
                self.context.request = {
                    'method': method,
                    'path': path,
                    'headers': {k: v for k, v in environ.items() if k.startswith('HTTP_')},
                    'query_string': environ['QUERY_STRING'],
                    'body': environ['wsgi.input'].read().decode()
                }
                response = func(**match.groupdict())
                start_response(response['status'], response['headers'])
                return [response['body'].encode()]
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'Not Found']

    def run(self, host='127.0.0.1', port=5000):
        with make_server(host, port, self) as server:
            print(f"Serving on http://{host}:{port}")
            server.serve_forever()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def render_template(self, template_name, **context):
        template = self.templates_env.get_template(template_name)
        return template.render(**context)

    @property
    def current_app(self):
        return self

    @property
    def g(self):
        if not hasattr(self.context, 'g'): self.context.g = {}
        return self.context.g
