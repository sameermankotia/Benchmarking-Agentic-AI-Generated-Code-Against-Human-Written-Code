"""HTTP request and response objects for Django-style WSGI framework."""

import json
from io import BytesIO
from typing import Dict, List, Optional, Union, Any
from urllib.parse import parse_qs, unquote


class HttpRequest:
    """Encapsulates an HTTP request."""
    
    def __init__(self, environ: Dict[str, Any]):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', 'GET').upper()
        self.path = unquote(environ.get('PATH_INFO', '/'))
        self.META = self._build_meta(environ)
        self.GET = self._parse_query_string(environ.get('QUERY_STRING', ''))
        self.POST = {}
        self.FILES = {}
        self.body = b''
        self._read_body()
    
    def _build_meta(self, environ: Dict[str, Any]) -> Dict[str, str]:
        """Build META dictionary from WSGI environ."""
        meta = {}
        
        # Copy all environ variables
        for key, value in environ.items():
            if isinstance(value, str):
                meta[key] = value
        
        # Add HTTP headers with HTTP_ prefix
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                # Convert HTTP_HEADER_NAME to Header-Name
                header_name = key[5:].replace('_', '-').title()
                meta[header_name] = value
        
        # Special cases for common headers
        if 'CONTENT_TYPE' in environ:
            meta['Content-Type'] = environ['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in environ:
            meta['Content-Length'] = environ['CONTENT_LENGTH']
        
        return meta
    
    def _parse_query_string(self, query_string: str) -> Dict[str, List[str]]:
        """Parse query string into a dictionary."""
        if not query_string:
            return {}
        
        parsed = parse_qs(query_string, keep_blank_values=True)
        return parsed
    
    def _read_body(self):
        """Read the request body."""
        try:
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0
        
        if content_length > 0:
            wsgi_input = self.environ.get('wsgi.input')
            if wsgi_input:
                self.body = wsgi_input.read(content_length)
                
                # Parse POST data for form submissions
                content_type = self.environ.get('CONTENT_TYPE', '')
                if content_type.startswith('application/x-www-form-urlencoded'):
                    self.POST = self._parse_query_string(self.body.decode('utf-8'))
    
    def get_full_path(self) -> str:
        """Get the full path including query string."""
        query_string = self.environ.get('QUERY_STRING', '')
        if query_string:
            return f"{self.path}?{query_string}"
        return self.path
    
    def is_secure(self) -> bool:
        """Return True if the request is secure (HTTPS)."""
        return self.environ.get('wsgi.url_scheme') == 'https'


class HttpResponse:
    """Encapsulates an HTTP response."""
    
    def __init__(self, content: Union[str, bytes] = '', 
                 content_type: str = 'text/html; charset=utf-8',
                 status: int = 200):
        self.status_code = status
        self.content = content
        self.headers = {'Content-Type': content_type}
        
    def __setitem__(self, key: str, value: str):
        """Set a response header."""
        self.headers[key] = value
    
    def __getitem__(self, key: str) -> str:
        """Get a response header."""
        return self.headers[key]
    
    def __delitem__(self, key: str):
        """Delete a response header."""
        del self.headers[key]
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a response header with default."""
        return self.headers.get(key, default)
    
    def set_cookie(self, key: str, value: str = '', max_age: Optional[int] = None,
                   expires: Optional[str] = None, path: str = '/', 
                   domain: Optional[str] = None, secure: bool = False,
                   httponly: bool = False, samesite: Optional[str] = None):
        """Set a cookie."""
        cookie_parts = [f"{key}={value}"]
        
        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        if expires:
            cookie_parts.append(f"Expires={expires}")
        if path:
            cookie_parts.append(f"Path={path}")
        if domain:
            cookie_parts.append(f"Domain={domain}")
        if secure:
            cookie_parts.append("Secure")
        if httponly:
            cookie_parts.append("HttpOnly")
        if samesite:
            cookie_parts.append(f"SameSite={samesite}")
        
        cookie_value = "; ".join(cookie_parts)
        
        # Handle multiple Set-Cookie headers
        if 'Set-Cookie' in self.headers:
            existing = self.headers['Set-Cookie']
            if isinstance(existing, list):
                existing.append(cookie_value)
            else:
                self.headers['Set-Cookie'] = [existing, cookie_value]
        else:
            self.headers['Set-Cookie'] = cookie_value
    
    def write(self, content: Union[str, bytes]):
        """Append content to the response."""
        if isinstance(self.content, str) and isinstance(content, str):
            self.content += content
        elif isinstance(self.content, bytes) and isinstance(content, bytes):
            self.content += content
        else:
            # Convert to bytes if mixed types
            if isinstance(self.content, str):
                self.content = self.content.encode('utf-8')
            if isinstance(content, str):
                content = content.encode('utf-8')
            self.content += content
    
    def get_content_as_bytes(self) -> bytes:
        """Get response content as bytes."""
        if isinstance(self.content, str):
            return self.content.encode('utf-8')
        return self.content
    
    def get_status_text(self) -> str:
        """Get HTTP status text for the status code."""
        status_texts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
            501: 'Not Implemented',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
        }
        return status_texts.get(self.status_code, 'Unknown')


class JsonResponse(HttpResponse):
    """HTTP response with JSON content."""
    
    def __init__(self, data: Any, status: int = 200, safe: bool = True,
                 json_dumps_params: Optional[Dict] = None):
        if json_dumps_params is None:
            json_dumps_params = {}
        
        if safe and not isinstance(data, dict):
            raise TypeError("In order to allow non-dict objects to be serialized "
                          "set the safe parameter to False.")
        
        content = json.dumps(data, **json_dumps_params)
        super().__init__(content, content_type='application/json', status=status)


class Http404(Exception):
    """Exception for 404 Not Found responses."""
    pass


class Http405(Exception):
    """Exception for 405 Method Not Allowed responses."""
    
    def __init__(self, allowed_methods: List[str]):
        self.allowed_methods = allowed_methods
        super().__init__(f"Method not allowed. Allowed: {', '.join(allowed_methods)}")


def HttpResponseNotFound(content: str = "Not Found") -> HttpResponse:
    """Create a 404 Not Found response."""
    return HttpResponse(content, status=404)


def HttpResponseNotAllowed(allowed_methods: List[str], 
                          content: str = "Method Not Allowed") -> HttpResponse:
    """Create a 405 Method Not Allowed response."""
    response = HttpResponse(content, status=405)
    response['Allow'] = ', '.join(allowed_methods)
    return response
