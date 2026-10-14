"""
HTTP response handling for Django-style framework.
"""


class HttpResponse:
    """
    HTTP response object carrying status code, headers, and body.
    """
    
    def __init__(self, content='', content_type='text/html; charset=utf-8', status=200):
        self.content = content
        self.status_code = status
        self._headers = {}
        
        # Set default content type
        self['Content-Type'] = content_type
    
    def __setitem__(self, header, value):
        """Set a header value."""
        self._headers[header.lower()] = (header, str(value))
    
    def __getitem__(self, header):
        """Get a header value."""
        return self._headers[header.lower()][1]
    
    def __delitem__(self, header):
        """Delete a header."""
        del self._headers[header.lower()]
    
    def __contains__(self, header):
        """Check if header exists."""
        return header.lower() in self._headers
    
    def get(self, header, default=None):
        """Get a header value with default."""
        try:
            return self[header]
        except KeyError:
            return default
    
    def items(self):
        """Return header items as (name, value) tuples."""
        return [item for item in self._headers.values()]
    
    @property
    def content_bytes(self):
        """Get content as bytes."""
        if isinstance(self.content, str):
            return self.content.encode('utf-8')
        return self.content
    
    def __iter__(self):
        """Make response iterable for WSGI."""
        yield self.content_bytes


class HttpResponseNotFound(HttpResponse):
    """404 Not Found response."""
    
    def __init__(self, content='Not Found', *args, **kwargs):
        super().__init__(content, status=404, *args, **kwargs)


class HttpResponseNotAllowed(HttpResponse):
    """405 Method Not Allowed response."""
    
    def __init__(self, permitted_methods, content='Method Not Allowed', *args, **kwargs):
        super().__init__(content, status=405, *args, **kwargs)
        self['Allow'] = ', '.join(permitted_methods)
