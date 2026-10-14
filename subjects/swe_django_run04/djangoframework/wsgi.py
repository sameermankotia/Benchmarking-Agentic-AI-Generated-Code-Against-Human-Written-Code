"""
WSGI application that handles URL routing and view dispatching.
"""
import traceback
from .http import HttpRequest, HttpResponse, Http404
from .urls import URLResolver


class WSGIApplication:
    """
    WSGI-compatible application that routes URLs and dispatches to views.
    """
    
    def __init__(self, urlpatterns):
        self.url_resolver = URLResolver(urlpatterns)
    
    def __call__(self, environ, start_response):
        """
        WSGI application entry point.
        """
        try:
            # Create request object
            request = HttpRequest(environ)
            
            # Resolve URL to view and kwargs
            # Strip leading slash to match Django's URL pattern behavior
            path_to_resolve = request.path.lstrip('/')
            try:
                view, kwargs = self.url_resolver.resolve(path_to_resolve)
            except Http404:
                response = HttpResponse(
                    content='<h1>404 Not Found</h1><p>The requested URL was not found on this server.</p>',
                    status=404
                )
            else:
                # Call the view
                try:
                    response = view(request, **kwargs)
                except Exception as e:
                    # Handle view exceptions
                    response = HttpResponse(
                        content=f'<h1>500 Internal Server Error</h1><pre>{traceback.format_exc()}</pre>',
                        status=500
                    )
            
            # Ensure we have a valid response
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
                content=f'<h1>500 Internal Server Error</h1><pre>{traceback.format_exc()}</pre>',
                status=500
            )
            
            status = f'{error_response.status_code} {error_response.get_status_text()}'
            headers = [(key, value) for key, value in error_response.headers.items()]
            
            content = b''.join(error_response)
            headers.append(('Content-Length', str(len(content))))
            
            start_response(status, headers)
            return [content]
