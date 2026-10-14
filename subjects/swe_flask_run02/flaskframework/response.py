"""
Response object with status code, headers, and body.
"""

from typing import Dict, List, Tuple, Union, Optional, Iterator


class Response:
    """HTTP response object with status code, headers, and body."""
    
    def __init__(self, response=None, status=200, headers=None, mimetype='text/html', content_type=None):
        if isinstance(response, str):
            self.data = response.encode('utf-8')
        elif isinstance(response, bytes):
            self.data = response
        elif response is None:
            self.data = b''
        else:
            # Convert other types to string then bytes
            self.data = str(response).encode('utf-8')
        
        self.status_code = status
        self.headers = {}
        
        # Set default headers
        if headers:
            if isinstance(headers, dict):
                self.headers.update(headers)
            else:
                # Assume it's a list of tuples
                for key, value in headers:
                    self.headers[key] = value
        
        # Set content type
        if content_type:
            self.headers['Content-Type'] = content_type
        elif mimetype and 'Content-Type' not in self.headers:
            if mimetype == 'text/html':
                self.headers['Content-Type'] = 'text/html; charset=utf-8'
            else:
                self.headers['Content-Type'] = mimetype
        
        # Set content length
        self.headers['Content-Length'] = str(len(self.data))
    
    @property
    def status(self) -> str:
        """Status line for HTTP response"""
        status_messages = {
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
            503: 'Service Unavailable'
        }
        message = status_messages.get(self.status_code, 'Unknown')
        return f'{self.status_code} {message}'
    
    def get_wsgi_headers(self) -> List[Tuple[str, str]]:
        """Get headers in WSGI format (list of tuples)"""
        return [(key, str(value)) for key, value in self.headers.items()]
    
    def __iter__(self) -> Iterator[bytes]:
        """Make response iterable for WSGI"""
        yield self.data


def make_response(rv, status=None, headers=None) -> Response:
    """Convert various return values to Response objects."""
    if isinstance(rv, Response):
        if status is not None:
            rv.status_code = status
        if headers:
            rv.headers.update(headers)
        return rv
    
    if isinstance(rv, tuple):
        if len(rv) == 2:
            rv, status = rv
        elif len(rv) == 3:
            rv, status, headers = rv
    
    return Response(rv, status or 200, headers)
