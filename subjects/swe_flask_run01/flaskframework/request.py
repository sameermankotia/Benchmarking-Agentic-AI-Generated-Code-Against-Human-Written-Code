"""
Request object encapsulating HTTP request data.
"""

import io
from urllib.parse import parse_qs, unquote


class Request:
    """Request object that encapsulates HTTP request data."""
    
    def __init__(self, environ):
        self.environ = environ
        self._body = None
        self._form = None
        self._args = None
    
    @property
    def method(self):
        """HTTP method (GET, POST, etc.)"""
        return self.environ.get('REQUEST_METHOD', 'GET')
    
    @property
    def path(self):
        """Request path"""
        return self.environ.get('PATH_INFO', '/')
    
    @property
    def headers(self):
        """Request headers as a dict-like object"""
        headers = {}
        for key, value in self.environ.items():
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
    def query_string(self):
        """Raw query string"""
        return self.environ.get('QUERY_STRING', '')
    
    @property
    def args(self):
        """Parsed query string arguments"""
        if self._args is None:
            self._args = parse_qs(self.query_string, keep_blank_values=True)
            # Convert lists to single values for convenience
            for key, value in self._args.items():
                if len(value) == 1:
                    self._args[key] = value[0]
        return self._args
    
    @property
    def body(self):
        """Request body as bytes"""
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
    def data(self):
        """Request body as string"""
        return self.body.decode('utf-8', errors='replace')
    
    @property
    def form(self):
        """Parsed form data (for POST requests)"""
        if self._form is None:
            content_type = self.environ.get('CONTENT_TYPE', '')
            if content_type.startswith('application/x-www-form-urlencoded'):
                self._form = parse_qs(self.data, keep_blank_values=True)
                # Convert lists to single values for convenience
                for key, value in self._form.items():
                    if len(value) == 1:
                        self._form[key] = value[0]
            else:
                self._form = {}
        return self._form
    
    def get_json(self):
        """Parse JSON body"""
        import json
        content_type = self.environ.get('CONTENT_TYPE', '')
        if content_type.startswith('application/json'):
            try:
                return json.loads(self.data)
            except json.JSONDecodeError:
                return None
        return None
