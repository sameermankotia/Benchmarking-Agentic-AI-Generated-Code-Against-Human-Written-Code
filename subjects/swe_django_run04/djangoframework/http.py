"""
HTTP request and response classes.
"""
import urllib.parse
from io import BytesIO


class HttpRequest:
    """
    Encapsulates HTTP request data including method, path, headers, 
    query string, and body.
    """
    
    def __init__(self, environ):
        self.environ = environ
        self.method = environ['REQUEST_METHOD']
        self.path = environ['PATH_INFO']
        self.query_string = environ.get('QUERY_STRING', '')
        
        # Parse headers from environ
        self.headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].replace('_', '-').title()
                self.headers[header_name] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.replace('_', '-').title()
                self.headers[header_name] = value
        
        # Read body
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0
            
        if content_length > 0 and environ.get('wsgi.input'):
            self.body = environ['wsgi.input'].read(content_length)
        else:
            self.body = b''
        
        # Parse query parameters
        self.GET = urllib.parse.parse_qs(self.query_string, keep_blank_values=True)
        
        # Parse POST data if applicable
        self.POST = {}
        if self.method == 'POST' and self.headers.get('Content-Type', '').startswith('application/x-www-form-urlencoded'):
            self.POST = urllib.parse.parse_qs(self.body.decode('utf-8'), keep_blank_values=True)


class HttpResponse:
    """
    HTTP response object carrying status code, headers, and body.
    """
    
    def __init__(self, content='', status=200, content_type='text/html; charset=utf-8'):
        self.content = content
        self.status_code = status
        self.headers = {'Content-Type': content_type}
        
    def __iter__(self):
        """Make response iterable for WSGI."""
        if isinstance(self.content, str):
            yield self.content.encode('utf-8')
        elif isinstance(self.content, bytes):
            yield self.content
        else:
            yield str(self.content).encode('utf-8')
    
    def get_status_text(self):
        """Get HTTP status text."""
        status_texts = {
            200: 'OK',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
        }
        return status_texts.get(self.status_code, 'Unknown')


class Http404(Exception):
    """Exception for 404 Not Found responses."""
    pass


class Http405(Exception):
    """Exception for 405 Method Not Allowed responses."""
    
    def __init__(self, allowed_methods):
        self.allowed_methods = allowed_methods
        super().__init__(f"Method not allowed. Allowed methods: {', '.join(allowed_methods)}")
