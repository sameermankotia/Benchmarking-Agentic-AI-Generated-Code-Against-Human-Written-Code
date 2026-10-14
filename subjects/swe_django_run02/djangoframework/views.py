"""
Class-based views implementation.
"""

from .http import HttpRequest, HttpResponse, HttpResponseNotAllowed


class View:
    """
    Base class for class-based views.
    
    Dispatches requests to methods named for HTTP verbs.
    Returns 405 with Allow header for unsupported methods.
    Serves HEAD from GET implementation.
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
        
        view.view_class = cls
        view.view_initkwargs = initkwargs
        
        return view
    
    def dispatch(self, request, *args, **kwargs):
        """
        Try to dispatch to the right method; if a method doesn't exist,
        defer to the error handler. Also defer to the error handler if the
        request method isn't on the approved list.
        """
        if request.method.lower() in self.http_method_names:
            handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        
        return handler(request, *args, **kwargs)
    
    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        Return a 405 Method Not Allowed response with the Allow header
        listing the methods this view supports.
        """
        allowed_methods = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allowed_methods.append(method.upper())
        
        # Special case: if GET is implemented, HEAD is automatically supported
        if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
            allowed_methods.append('HEAD')
        
        return HttpResponseNotAllowed(allowed_methods)
    
    def options(self, request, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        allowed_methods = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allowed_methods.append(method.upper())
        
        # Special case: if GET is implemented, HEAD is automatically supported
        if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
            allowed_methods.append('HEAD')
        
        response = HttpResponse()
        response.headers['Allow'] = ', '.join(allowed_methods)
        return response
    
    def head(self, request, *args, **kwargs):
        """
        Handle HEAD requests by calling GET and returning empty content.
        """
        if hasattr(self, 'get'):
            response = self.get(request, *args, **kwargs)
            # Clear the content for HEAD requests
            response.content = ''
            return response
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)
