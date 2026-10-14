"""
Request object encapsulating HTTP request data.
"""
import urllib.parse
from io import StringIO


class Request:
    """Request object that encapsulates HTTP request data."""
    
    def __init__(self, environ):
        self.environ = environ
        self._body = None
        self._json = None
        
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
                # Convert HTTP_CONTENT_TYPE to Content-Type
                header_name = key[5:].replace('_', '-').title()
                headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.replace('_', '-').title()
                headers[header_name] = value
        return headers
    
    @property
    def query_string(self):
        """Query string as bytes"""
        return self.environ.get('QUERY_STRING', '').encode('latin1')
    
    @property
    def args(self):
        """Parsed query string arguments"""
        qs = self.environ.get('QUERY_STRING', '')
        return urllib.parse.parse_qs(qs, keep_blank_values=True)
    
    @property
    def body(self):
        """Request body as bytes"""
        if self._body is None:
            try:
                content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            except ValueError:
                content_length = 0
            
            if content_length > 0:
                wsgi_input = self.environ.get('wsgi.input')
                if wsgi_input:
                    data = wsgi_input.read(content_length)
                    # Handle both bytes and string input
                    if isinstance(data, str):
                        self._body = data.encode('utf-8')
                    else:
                        self._body = data
                else:
                    self._body = b''
            else:
                self._body = b''
        return self._body
    
    @property
    def data(self):
        """Request body as string"""
        return self.body.decode('utf-8', errors='replace')
    
    def get_json(self):
        """Parse request body as JSON"""
        if self._json is None:
            try:
                import json
                self._json = json.loads(self.data)
            except (ValueError, TypeError):
                self._json = None
        return self._json
