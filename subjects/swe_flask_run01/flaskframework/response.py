"""
Response object with status code, headers, and body.
"""

import json
from typing import Union, Dict, List, Tuple, Any


class Response:
    """Response object that encapsulates HTTP response data."""
    
    def __init__(self, response=None, status=200, headers=None, mimetype='text/html'):
        if isinstance(response, str):
            self.data = response.encode('utf-8')
        elif isinstance(response, bytes):
            self.data = response
        elif response is None:
            self.data = b''
        else:
            # Convert other types to JSON
            self.data = json.dumps(response).encode('utf-8')
            mimetype = 'application/json'
        
        self.status_code = status
        self.headers = dict(headers or {})
        
        # Set content type if not already set
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = mimetype
        
        # Set content length
        self.headers['Content-Length'] = str(len(self.data))
    
    @property
    def status(self):
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
            502: 'Bad Gateway',
            503: 'Service Unavailable',
        }
        message = status_messages.get(self.status_code, 'Unknown')
        return f"{self.status_code} {message}"
    
    def set_cookie(self, key, value='', max_age=None, expires=None, path='/', 
                   domain=None, secure=False, httponly=False):
        """Set a cookie"""
        cookie = f"{key}={value}; Path={path}"
        
        if max_age is not None:
            cookie += f"; Max-Age={max_age}"
        
        if expires is not None:
            cookie += f"; Expires={expires}"
        
        if domain is not None:
            cookie += f"; Domain={domain}"
        
        if secure:
            cookie += "; Secure"
        
        if httponly:
            cookie += "; HttpOnly"
        
        # Handle multiple Set-Cookie headers
        if 'Set-Cookie' in self.headers:
            if isinstance(self.headers['Set-Cookie'], list):
                self.headers['Set-Cookie'].append(cookie)
            else:
                self.headers['Set-Cookie'] = [self.headers['Set-Cookie'], cookie]
        else:
            self.headers['Set-Cookie'] = cookie
    
    def __iter__(self):
        """Make response iterable for WSGI"""
        yield self.data


def make_response(rv, status=None, headers=None):
    """Create a Response object from various return values"""
    if isinstance(rv, Response):
        if status is not None:
            rv.status_code = status
        if headers is not None:
            rv.headers.update(headers)
        return rv
    
    if isinstance(rv, tuple):
        if len(rv) == 2:
            rv, status = rv
        elif len(rv) == 3:
            rv, status, headers = rv
    
    return Response(rv, status or 200, headers)
