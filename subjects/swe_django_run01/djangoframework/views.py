"""
Class-based views for Django-style framework.
"""

from .response import HttpResponse, HttpResponseNotAllowed


class View:
    """
    Base class-based view that dispatches requests to methods named for HTTP verbs.
    """
    
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
    
    def __init__(self, **kwargs):
        """Initialize the view instance."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        Returns a view function that can be used in URL patterns.
        """
        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            return self.dispatch(request, *args, **kwargs)
        
        # Copy class attributes to the view function
        view.view_class = cls
        view.view_initkwargs = initkwargs
        
        return view
    
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch the request to the appropriate handler method.
        """
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        
        # Handle HEAD requests by using GET handler if available
        if request.method.upper() == 'HEAD' and not hasattr(self, 'head'):
            if hasattr(self, 'get'):
                handler = self.get
        
        return handler(request, *args, **kwargs)
    
    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        Return a 405 Method Not Allowed response with appropriate Allow header.
        """
        allowed_methods = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allowed_methods.append(method.upper())
        
        # If we have a GET method, HEAD is also allowed
        if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
            allowed_methods.append('HEAD')
        
        return HttpResponseNotAllowed(allowed_methods)
    
    def options(self, request, *args, **kwargs):
        """Handle OPTIONS requests by returning allowed methods."""
        allowed_methods = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allowed_methods.append(method.upper())
        
        # If we have a GET method, HEAD is also allowed
        if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
            allowed_methods.append('HEAD')
        
        # Always allow OPTIONS
        if 'OPTIONS' not in allowed_methods:
            allowed_methods.append('OPTIONS')
        
        response = HttpResponse()
        response['Allow'] = ', '.join(sorted(allowed_methods))
        return response
