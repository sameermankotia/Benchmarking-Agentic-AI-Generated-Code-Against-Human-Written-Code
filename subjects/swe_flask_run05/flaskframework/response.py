"""
Response object for HTTP responses.
"""


class Response:
    """Response object with status code, headers, and body."""
    
    def __init__(self, response=None, status=200, headers=None, mimetype='text/html'):
        if response is None:
            self.data = b''
        elif isinstance(response, str):
            self.data = response.encode('utf-8')
        elif isinstance(response, bytes):
            self.data = response
        else:
            self.data = str(response).encode('utf-8')
            
        self.status_code = status
        self.headers = headers or {}
        
        # Set content type if not already set
        if 'Content-Type' not in self.headers:
            if mimetype:
                self.headers['Content-Type'] = mimetype
    
    @property
    def status(self):
        """Status line for WSGI"""
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
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        }
        status_text = status_texts.get(self.status_code, 'Unknown')
        return f"{self.status_code} {status_text}"
    
    def get_wsgi_headers(self):
        """Convert headers to WSGI format"""
        wsgi_headers = []
        for name, value in self.headers.items():
            wsgi_headers.append((name, str(value)))
        
        # Add content length if not present
        if 'Content-Length' not in self.headers:
            wsgi_headers.append(('Content-Length', str(len(self.data))))
            
        return wsgi_headers
    
    def __iter__(self):
        """Make response iterable for WSGI"""
        yield self.data
