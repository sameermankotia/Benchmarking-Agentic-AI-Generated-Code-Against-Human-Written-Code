"""
WSGI application for Django-style framework.
"""

from .request import HttpRequest
from .response import HttpResponseNotFound
from .urls import URLResolver


class WSGIApplication:
    """
    WSGI-compatible application that handles URL routing and view dispatching.
    """
    
    def __init__(self, urlpatterns):
        self.resolver = URLResolver(urlpatterns)
    
    def __call__(self, environ, start_response):
        """
        WSGI application callable.
        """
        # Create request object
        request = HttpRequest(environ)
        
        # Try to resolve the URL
        resolver_match = self.resolver.resolve(request.path)
        
        if resolver_match is None:
            # No pattern matched, return 404
            response = HttpResponseNotFound()
        else:
            # Set resolver match on request
            request.resolver_match = resolver_match
            request.url_kwargs = resolver_match.kwargs
            
            try:
                # Call the view function
                response = resolver_match.func(request, *resolver_match.args, **resolver_match.kwargs)
            except Exception as e:
                # In a real framework, this would be handled by middleware
                # For now, return a simple 500 error
                from .response import HttpResponse
                response = HttpResponse(f'Internal Server Error: {str(e)}', status=500)
        
        # Prepare WSGI response
        status = f'{response.status_code} {self._get_status_text(response.status_code)}'
        headers = list(response.items())
        
        # Start the response
        start_response(status, headers)
        
        # Return response body as iterable
        return [response.content_bytes]
    
    def _get_status_text(self, status_code):
        """Get HTTP status text for status code."""
        status_texts = {
            200: 'OK',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
        }
        return status_texts.get(status_code, 'Unknown')
