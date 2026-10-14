"""
Request object encapsulating HTTP request data.
"""

import io
from urllib.parse import parse_qs, unquote_plus
from typing import Dict, Any, Optional


class Request:
    """Request object encapsulating method, path, headers, query string, and body."""
    
    def __init__(self, environ: Dict[str, Any]):
        self.environ = environ
        self._body = None
        self._form = None
        self._args = None
    
    @property
    def method(self) -> str:
        """HTTP method (GET, POST, etc.)."""
        return self.environ.get('REQUEST_METHOD', 'GET')
    
    @property
    def path(self) -> str:
        """Request path."""
        return self.environ.get('PATH_INFO', '/')
    
    @property
    def query_string(self) -> str:
        """Raw query string."""
        return self.environ.get('QUERY_STRING', '')
    
    @property
    def headers(self) -> Dict[str, str]:
        """Request headers."""
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
    def args(self) -> Dict[str, str]:
        """Parsed query string arguments."""
        if self._args is None:
            self._args = {}
            if self.query_string:
                parsed = parse_qs(self.query_string, keep_blank_values=True)
                # Convert lists to single values (take first value)
                for key, values in parsed.items():
                    self._args[key] = values[0] if values else ''
        return self._args
    
    @property
    def body(self) -> bytes:
        """Request body as bytes."""
        if self._body is None:
            try:
                content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            except ValueError:
                content_length = 0
            
            if content_length > 0:
                wsgi_input = self.environ.get('wsgi.input')
                if wsgi_input:
                    self._body = wsgi_input.read(content_length)
                else:
                    self._body = b''
            else:
                self._body = b''
        return self._body
    
    @property
    def data(self) -> str:
        """Request body as string."""
        return self.body.decode('utf-8', errors='replace')
    
    @property
    def form(self) -> Dict[str, str]:
        """Parsed form data (for POST requests)."""
        if self._form is None:
            self._form = {}
            content_type = self.environ.get('CONTENT_TYPE', '')
            if content_type.startswith('application/x-www-form-urlencoded'):
                body_str = self.data
                if body_str:
                    parsed = parse_qs(body_str, keep_blank_values=True)
                    # Convert lists to single values (take first value)
                    for key, values in parsed.items():
                        self._form[key] = values[0] if values else ''
        return self._form
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a specific header value."""
        return self.headers.get(name.title(), default)
