"""
Class-based views with HTTP method dispatch.
"""
from .http import HttpResponse, Http405


class View:
    """
    Base class for class-based views that dispatch requests to methods
    named for the HTTP verb.
    """
    
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
    
    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
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
        Handle requests for methods not implemented by this view.
        Returns 405 with Allow header listing implemented methods.
        """
        allowed_methods = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allowed_methods.append(method.upper())
        
        # Handle HEAD requests if GET is implemented
        if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
            allowed_methods.append('HEAD')
        
        response = HttpResponse(
            content=f'Method {request.method} not allowed.',
            status=405
        )
        response.headers['Allow'] = ', '.join(allowed_methods)
        return response
    
    def head(self, request, *args, **kwargs):
        """
        Handle HEAD requests by calling GET and returning empty body.
        """
        if hasattr(self, 'get'):
            response = self.get(request, *args, **kwargs)
            # Clear the content for HEAD requests
            response.content = ''
            return response
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)
