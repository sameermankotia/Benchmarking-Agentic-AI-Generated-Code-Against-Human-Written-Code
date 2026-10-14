"""
Response object implementation.
"""


class Response:
    """Response object with status code, headers, and body."""
    
    def __init__(self, body='', status=200, headers=None, content_type='text/html'):
        self.body = body
        self.status_code = status
        self.headers = headers or {}
        
        # Set default content type if not provided
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = content_type
    
    @property
    def status(self):
        """Get status line for WSGI."""
        status_messages = {
            200: 'OK',
            201: 'Created',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
        }
        message = status_messages.get(self.status_code, 'Unknown')
        return f"{self.status_code} {message}"
    
    def get_wsgi_headers(self):
        """Get headers in WSGI format (list of tuples)."""
        return list(self.headers.items())
    
    def get_body_bytes(self):
        """Get body as bytes for WSGI."""
        if isinstance(self.body, str):
            return self.body.encode('utf-8')
        elif isinstance(self.body, bytes):
            return self.body
        else:
            return str(self.body).encode('utf-8')
