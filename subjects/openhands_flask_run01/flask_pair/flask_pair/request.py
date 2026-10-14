
from urllib.parse import parse_qs

class Request:
    def __init__(self, environ):
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO']
        self.headers = {key[5:]: value for key, value in environ.items() if key.startswith('HTTP_')}
        self.query = parse_qs(environ['QUERY_STRING'])
        self.body = environ['wsgi.input'].read().decode()