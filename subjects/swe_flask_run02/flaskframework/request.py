"""
Request object that encapsulates HTTP request data.
"""

import io
from urllib.parse import parse_qs, unquote
from typing import Dict, Any, Optional


class Request:
    """Encapsulates HTTP request data including method, path, headers, query string, and body."""
    
    def __init__(self, environ):
        self.environ = environ
        self._body = None
        self._json = None
    
    @property
    def method(self) -> str:
        """HTTP method (GET, POST, etc.)"""
        return self.environ.get('REQUEST_METHOD', 'GET')
    
    @property
    def path(self) -> str:
        """Request path"""
        return self.environ.get('PATH_INFO', '/')
    
    @property
    def query_string(self) -> str:
        """Raw query string"""
        return self.environ.get('QUERY_STRING', '')
    
    @property
    def args(self) -> Dict[str, Any]:
        """Parsed query string arguments"""
        if not hasattr(self, '_args'):
            self._args = {}
            if self.query_string:
                parsed = parse_qs(self.query_string, keep_blank_values=True)
                # Convert lists to single values for simplicity
                for key, values in parsed.items():
                    self._args[key] = values[0] if len(values) == 1 else values
        return self._args
    
    @property
    def headers(self) -> Dict[str, str]:
        """HTTP headers"""
        if not hasattr(self, '_headers'):
            self._headers = {}
            for key, value in self.environ.items():
                if key.startswith('HTTP_'):
                    # Convert HTTP_CONTENT_TYPE to Content-Type
                    header_name = key[5:].replace('_', '-').title()
                    self._headers[header_name] = value
                elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    # Special case for content headers
                    header_name = key.replace('_', '-').title()
                    self._headers[header_name] = value
        return self._headers
    
    @property
    def content_type(self) -> Optional[str]:
        """Content type header"""
        return self.environ.get('CONTENT_TYPE')
    
    @property
    def content_length(self) -> Optional[int]:
        """Content length header"""
        length = self.environ.get('CONTENT_LENGTH')
        return int(length) if length else None
    
    @property
    def body(self) -> bytes:
        """Request body as bytes"""
        if self._body is None:
            wsgi_input = self.environ.get('wsgi.input')
            if wsgi_input:
                content_length = self.content_length
                if content_length:
                    self._body = wsgi_input.read(content_length)
                else:
                    self._body = wsgi_input.read()
            else:
                self._body = b''
        return self._body
    
    @property
    def data(self) -> str:
        """Request body as string"""
        return self.body.decode('utf-8', errors='replace')
    
    def get_json(self) -> Any:
        """Parse JSON from request body"""
        if self._json is None and self.content_type and 'application/json' in self.content_type:
            try:
                import json
                self._json = json.loads(self.data)
            except (ValueError, json.JSONDecodeError):
                self._json = None
        return self._json
