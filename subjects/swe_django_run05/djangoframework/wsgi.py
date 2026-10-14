"""WSGI application for Django-like framework."""

import traceback
from typing import List, Callable, Dict, Any, Iterable
from .http import HttpRequest, HttpResponse, HttpResponseNotFound
from .urls import URLPattern, URLResolver


class WSGIApplication:
    """WSGI application that handles URL routing and view dispatching."""
    
    def __init__(self, urlpatterns: List[URLPattern]):
        self.urlpatterns = urlpatterns
        self.resolver = URLResolver(urlpatterns)
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        """WSGI application callable."""
        try:
            # Create request object
            request = HttpRequest(environ)
            
            # Resolve URL to view and parameters
            try:
                view_func, kwargs = self.resolver.resolve(request.path)
                
                # Call the view function
                response = view_func(request, **kwargs)
                
                # Ensure we have an HttpResponse object
                if not isinstance(response, HttpResponse):
                    response = HttpResponse(str(response))
                
            except ValueError:
                # No URL pattern matched - return 404
                response = HttpResponseNotFound()
            except Exception as e:
                # Internal server error
                response = HttpResponse(
                    f"Internal Server Error: {str(e)}\n\n{traceback.format_exc()}",
                    status=500,
                    content_type='text/plain'
                )
            
            # Prepare response headers
            response_headers = []
            for key, value in response.headers.items():
                response_headers.append((key, value))
            
            # Add content length header
            content = response.content.encode('utf-8') if isinstance(response.content, str) else response.content
            response_headers.append(('Content-Length', str(len(content))))
            
            # Start the response
            start_response(response.get_status_text(), response_headers)
            
            # Return response content
            return [content]
            
        except Exception as e:
            # Fallback error handling
            error_response = f"500 Internal Server Error: {str(e)}"
            start_response('500 Internal Server Error', [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(error_response)))
            ])
            return [error_response.encode('utf-8')]


def get_wsgi_application(urlpatterns: List[URLPattern]) -> WSGIApplication:
    """Create and return a WSGI application."""
    return WSGIApplication(urlpatterns)
