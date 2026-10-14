"""
Response object with status code, headers, and body.
"""

from typing import Dict, List, Tuple, Union, Optional, Iterator


class Response:
    """Response object with status code, headers, and body."""
    
    def __init__(self, 
                 response: Union[str, bytes, Iterator[bytes]] = '',
                 status: int = 200,
                 headers: Optional[Dict[str, str]] = None,
                 mimetype: str = 'text/html',
                 content_type: Optional[str] = None):
        
        self.status_code = status
        self.headers = headers or {}
        
        # Set content type
        if content_type:
            self.headers['Content-Type'] = content_type
        elif 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = mimetype
        
        # Handle response data
        if isinstance(response, str):
            self.data = response.encode('utf-8')
        elif isinstance(response, bytes):
            self.data = response
        else:
            # Iterator of bytes
            self.data = b''.join(response)
        
        # Set content length if not already set
        if 'Content-Length' not in self.headers:
            self.headers['Content-Length'] = str(len(self.data))
    
    @property
    def status(self) -> str:
        """Status line for HTTP response."""
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
        """Get headers in WSGI format (list of tuples)."""
        return [(name, value) for name, value in self.headers.items()]
    
    def set_header(self, name: str, value: str) -> None:
        """Set a response header."""
        self.headers[name] = value
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a response header."""
        return self.headers.get(name, default)
    
    def __iter__(self) -> Iterator[bytes]:
        """Make response iterable for WSGI."""
        yield self.data


def make_response(rv: Union[str, bytes, dict, Response, Tuple]) -> Response:
    """Convert various return values to Response objects."""
    if isinstance(rv, Response):
        return rv
    
    if isinstance(rv, dict):
        # Convert dictionary to JSON
        import json
        json_str = json.dumps(rv)
        return Response(json_str, mimetype='application/json')
    
    if isinstance(rv, tuple):
        if len(rv) == 2:
            # (response, status) or (response, headers)
            response, second = rv
            if isinstance(second, int):
                # Handle dict response with status
                if isinstance(response, dict):
                    import json
                    json_str = json.dumps(response)
                    return Response(json_str, status=second, mimetype='application/json')
                return Response(response, status=second)
            elif isinstance(second, dict):
                return Response(response, headers=second)
        elif len(rv) == 3:
            # (response, status, headers)
            response, status, headers = rv
            if isinstance(response, dict):
                import json
                json_str = json.dumps(response)
                return Response(json_str, status=status, headers=headers, mimetype='application/json')
            return Response(response, status=status, headers=headers)
    
    # Default case: string or bytes
    return Response(rv)
