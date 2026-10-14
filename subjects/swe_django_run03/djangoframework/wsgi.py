"""WSGI application for Django-style URL routing and view dispatching."""

import traceback
from typing import List, Callable, Iterator, Union, Any, Dict
from .http import HttpRequest, HttpResponse, HttpResponseNotFound
from .urls import URLResolver, URLPattern, RegexURLPattern, Http404


class WSGIApplication:
    """WSGI application that handles URL routing and view dispatching."""
    
    def __init__(self, urlpatterns: List[Union[URLPattern, RegexURLPattern]]):
        self.resolver = URLResolver(urlpatterns)
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Iterator[bytes]:
        """WSGI application callable."""
        try:
            # Create request object
            request = HttpRequest(environ)
            
            # Resolve URL to view and kwargs
            # Strip leading slash for URL pattern matching (Django-style)
            path_for_matching = request.path.lstrip('/')
            try:
                view_func, kwargs = self.resolver.resolve(path_for_matching)
            except Http404:
                response = HttpResponseNotFound()
            else:
                # Call the view function
                try:
                    response = view_func(request, **kwargs)
                except Exception as e:
                    # Handle view exceptions
                    response = self._handle_view_exception(e, request)
            
            # Ensure we have an HttpResponse object
            if not isinstance(response, HttpResponse):
                response = HttpResponse(str(response))
            
            # Start the response
            status = f"{response.status_code} {response.get_status_text()}"
            headers = list(response.headers.items())
            
            # Handle multiple Set-Cookie headers
            cookie_headers = []
            other_headers = []
            for name, value in headers:
                if name.lower() == 'set-cookie':
                    if isinstance(value, list):
                        for cookie in value:
                            cookie_headers.append(('Set-Cookie', cookie))
                    else:
                        cookie_headers.append(('Set-Cookie', value))
                else:
                    other_headers.append((name, value))
            
            final_headers = other_headers + cookie_headers
            start_response(status, final_headers)
            
            # Return response content
            content = response.get_content_as_bytes()
            return [content]
            
        except Exception as e:
            # Handle application-level exceptions
            return self._handle_application_exception(e, environ, start_response)
    
    def _handle_view_exception(self, exception: Exception, request: HttpRequest) -> HttpResponse:
        """Handle exceptions raised by view functions."""
        # In a production application, this would log the error
        # and return a proper error page
        error_content = f"Internal Server Error: {str(exception)}"
        return HttpResponse(error_content, status=500)
    
    def _handle_application_exception(self, exception: Exception, environ: Dict[str, Any], 
                                    start_response: Callable) -> Iterator[bytes]:
        """Handle exceptions at the application level."""
        try:
            # Try to return a 500 error response
            status = "500 Internal Server Error"
            headers = [('Content-Type', 'text/plain; charset=utf-8')]
            start_response(status, headers)
            
            error_message = f"Application Error: {str(exception)}"
            return [error_message.encode('utf-8')]
        except:
            # If even error handling fails, return minimal response
            status = "500 Internal Server Error"
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b"Internal Server Error"]


def get_wsgi_application(urlpatterns: List[Union[URLPattern, RegexURLPattern]]) -> WSGIApplication:
    """Create and return a WSGI application."""
    return WSGIApplication(urlpatterns)
