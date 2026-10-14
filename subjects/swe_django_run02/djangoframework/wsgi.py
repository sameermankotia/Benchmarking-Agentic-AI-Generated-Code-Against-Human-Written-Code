"""
WSGI application implementation.
"""

import traceback
from typing import List, Union, Callable

from .http import HttpRequest, HttpResponse, HttpResponseNotFound, Http404
from .urls import URLPattern, RegexURLPattern, URLResolver


class WSGIApplication:
    """
    WSGI-compatible application that handles URL routing and view dispatching.
    """
    
    def __init__(self, urlpatterns: List[Union[URLPattern, RegexURLPattern]]):
        """Initialize the WSGI application with URL patterns."""
        self.resolver = URLResolver(urlpatterns)
    
    def __call__(self, environ, start_response):
        """
        WSGI application callable.
        
        Args:
            environ: WSGI environment dictionary
            start_response: WSGI start_response callable
        
        Returns:
            Iterable of response body bytes
        """
        try:
            # Create request object
            request = HttpRequest(environ)
            
            # Resolve URL to view and parameters
            try:
                view, kwargs = self.resolver.resolve(request.path)
            except Http404:
                response = HttpResponseNotFound()
            else:
                # Call the view with request and captured parameters
                try:
                    response = view(request, **kwargs)
                except Exception as e:
                    # Handle view exceptions
                    response = HttpResponse(
                        f'Internal Server Error: {str(e)}',
                        status=500,
                        content_type='text/plain'
                    )
            
            # Ensure we have an HttpResponse object
            if not isinstance(response, HttpResponse):
                response = HttpResponse(str(response))
            
            # Start the response
            status = f'{response.status_code} {response.get_status_text()}'
            headers = [(key, value) for key, value in response.headers.items()]
            
            # Add Content-Length header
            content = b''.join(response)
            headers.append(('Content-Length', str(len(content))))
            
            start_response(status, headers)
            
            # Return response content
            return [content]
            
        except Exception as e:
            # Handle any unexpected errors
            error_response = HttpResponse(
                f'Internal Server Error: {str(e)}\n\n{traceback.format_exc()}',
                status=500,
                content_type='text/plain'
            )
            
            status = f'{error_response.status_code} {error_response.get_status_text()}'
            headers = [(key, value) for key, value in error_response.headers.items()]
            
            content = b''.join(error_response)
            headers.append(('Content-Length', str(len(content))))
            
            start_response(status, headers)
            return [content]


def get_wsgi_application(urlpatterns: List[Union[URLPattern, RegexURLPattern]]) -> WSGIApplication:
    """
    Create and return a WSGI application.
    
    Args:
        urlpatterns: List of URL patterns
    
    Returns:
        WSGIApplication instance
    """
    return WSGIApplication(urlpatterns)
