"""
Request object implementation.
"""
import urllib.parse
from io import BytesIO


class Request:
    """Request object encapsulating method, path, headers, query string, and body."""
    
    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', 'GET')
        self.path = environ.get('PATH_INFO', '/')
        self.query_string = environ.get('QUERY_STRING', '')
        self.headers = self._get_headers(environ)
        self._body = None
        
    def _get_headers(self, environ):
        """Extract headers from WSGI environ."""
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                # Convert HTTP_HEADER_NAME to Header-Name
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                # Special case for content headers
                header_name = key.replace('_', '-').title()
                headers[header_name] = value
        return headers
    
    @property
    def body(self):
        """Get request body as bytes."""
        if self._body is None:
            try:
                content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            except ValueError:
                content_length = 0
            
            if content_length > 0:
                self._body = self.environ['wsgi.input'].read(content_length)
            else:
                self._body = b''
        return self._body
    
    @property
    def args(self):
        """Get query string parameters as a dict."""
        if not self.query_string:
            return {}
        return dict(urllib.parse.parse_qsl(self.query_string))
    
    @property
    def json(self):
        """Get JSON data from request body."""
        import json
        if self.headers.get('Content-Type', '').startswith('application/json'):
            return json.loads(self.body.decode('utf-8'))
        return None
