"""
HTTP request handling for Django-style framework.
"""

import urllib.parse
from io import BytesIO


class HttpRequest:
    """
    Encapsulates an HTTP request with method, path, headers, query string, and body.
    """
    
    def __init__(self, environ):
        self.environ = environ
        self.method = environ['REQUEST_METHOD'].upper()
        self.path = environ['PATH_INFO']
        self.META = {}
        
        # Convert WSGI environ to Django-style META
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                # Convert HTTP_HEADER_NAME to Header-Name
                header_name = key[5:].replace('_', '-').title()
                self.META[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                self.META[key.replace('_', '-').title()] = value
            else:
                self.META[key] = value
        
        # Parse query string
        self.GET = {}
        query_string = environ.get('QUERY_STRING', '')
        if query_string:
            parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            for key, values in parsed.items():
                # Django typically returns the last value for duplicate keys
                self.GET[key] = values[-1] if values else ''
        
        # Handle request body
        self._body = None
        self.content_length = int(environ.get('CONTENT_LENGTH', 0) or 0)
        
        # URL resolver will set these
        self.resolver_match = None
        self.url_kwargs = {}
    
    @property
    def body(self):
        """Get the request body as bytes."""
        if self._body is None:
            if self.content_length > 0:
                wsgi_input = self.environ.get('wsgi.input')
                if wsgi_input:
                    self._body = wsgi_input.read(self.content_length)
                else:
                    self._body = b''
            else:
                self._body = b''
        return self._body
    
    def get_full_path(self):
        """Return the full path including query string."""
        query_string = self.environ.get('QUERY_STRING', '')
        if query_string:
            return f"{self.path}?{query_string}"
        return self.path
