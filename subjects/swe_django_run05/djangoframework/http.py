"""HTTP request and response objects for Django-like framework."""

import json
from urllib.parse import parse_qs
from typing import Dict, List, Any, Optional


class HttpRequest:
    """Encapsulates an HTTP request with method, path, headers, query string, and body."""
    
    def __init__(self, environ: Dict[str, Any]):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', 'GET')
        self.path = environ.get('PATH_INFO', '/')
        self.query_string = environ.get('QUERY_STRING', '')
        
        # Parse headers from environ
        self.headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                self.headers[header_name] = value
        
        # Add content type and length if present
        if 'CONTENT_TYPE' in environ:
            self.headers['Content-Type'] = environ['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in environ:
            self.headers['Content-Length'] = environ['CONTENT_LENGTH']
        
        # Parse query parameters
        self.GET = parse_qs(self.query_string, keep_blank_values=True)
        
        # Read body
        self._body = None
        self.POST = {}
        
    @property
    def body(self) -> bytes:
        """Get the request body as bytes."""
        if self._body is None:
            try:
                content_length = int(self.environ.get('CONTENT_LENGTH', 0))
                if content_length > 0:
                    self._body = self.environ['wsgi.input'].read(content_length)
                else:
                    self._body = b''
            except (ValueError, KeyError):
                self._body = b''
        return self._body
    
    def get_full_path(self) -> str:
        """Get the full path including query string."""
        if self.query_string:
            return f"{self.path}?{self.query_string}"
        return self.path


class HttpResponse:
    """Encapsulates an HTTP response with status code, headers, and body."""
    
    def __init__(self, content: str = '', status: int = 200, content_type: str = 'text/html'):
        self.content = content
        self.status_code = status
        self.headers = {'Content-Type': content_type}
        
    def __iter__(self):
        """Make response iterable for WSGI."""
        yield self.content.encode('utf-8')
        
    def get_status_text(self) -> str:
        """Get the status line for HTTP response."""
        status_texts = {
            200: 'OK',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
        }
        return f"{self.status_code} {status_texts.get(self.status_code, 'Unknown')}"


class HttpResponseNotFound(HttpResponse):
    """404 Not Found response."""
    
    def __init__(self, content: str = 'Not Found'):
        super().__init__(content, status=404)


class HttpResponseNotAllowed(HttpResponse):
    """405 Method Not Allowed response."""
    
    def __init__(self, permitted_methods: List[str], content: str = 'Method Not Allowed'):
        super().__init__(content, status=405)
        self.headers['Allow'] = ', '.join(permitted_methods)


class JsonResponse(HttpResponse):
    """JSON response."""
    
    def __init__(self, data: Any, status: int = 200):
        content = json.dumps(data)
        super().__init__(content, status=status, content_type='application/json')
