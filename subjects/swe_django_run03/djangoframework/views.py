"""View classes and utilities for Django-style WSGI framework."""

from typing import List, Optional, Any
from .http import HttpRequest, HttpResponse, HttpResponseNotAllowed


class View:
    """Base class for class-based views."""
    
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
    
    def __init__(self, **kwargs):
        """Initialize the view instance."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def as_view(cls, **initkwargs):
        """Return a view function that instantiates and dispatches to the view."""
        
        def view(request: HttpRequest, *args, **kwargs):
            # Create view instance
            self = cls(**initkwargs)
            
            # Set request and args on the instance
            self.request = request
            self.args = args
            self.kwargs = kwargs
            
            # Dispatch to the appropriate method
            return self.dispatch(request, *args, **kwargs)
        
        # Copy class attributes to the view function
        view.view_class = cls
        view.view_initkwargs = initkwargs
        
        return view
    
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch the request to the appropriate handler method."""
        method = request.method.lower()
        
        # Handle HEAD requests by delegating to GET if available
        if method == 'head' and not hasattr(self, 'head'):
            if hasattr(self, 'get'):
                method = 'get'
        
        # Check if method is allowed
        if method in self.http_method_names and hasattr(self, method):
            handler = getattr(self, method)
            response = handler(request, *args, **kwargs)
            
            # For HEAD requests, clear the content but keep headers
            if request.method.upper() == 'HEAD' and method == 'get':
                response.content = ''
            
            return response
        else:
            # Method not allowed - return 405 with Allow header
            allowed_methods = [m.upper() for m in self.http_method_names 
                             if hasattr(self, m)]
            
            # Add HEAD if GET is available
            if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
                allowed_methods.append('HEAD')
            
            return HttpResponseNotAllowed(allowed_methods)
    
    def http_method_not_allowed(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle requests for unsupported HTTP methods."""
        allowed_methods = [m.upper() for m in self.http_method_names 
                         if hasattr(self, m)]
        return HttpResponseNotAllowed(allowed_methods)


class TemplateView(View):
    """A view that renders a template."""
    
    template_name: Optional[str] = None
    content_type: str = 'text/html'
    
    def get_template_name(self) -> str:
        """Get the template name to render."""
        if self.template_name is None:
            raise ValueError("TemplateView requires either a 'template_name' "
                           "attribute or an implementation of 'get_template_name()'")
        return self.template_name
    
    def get_context_data(self, **kwargs) -> dict:
        """Get the context data for template rendering."""
        return kwargs
    
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET requests."""
        context = self.get_context_data(**kwargs)
        template_name = self.get_template_name()
        
        # Simple template rendering - just return the template name and context
        # In a real implementation, this would use a template engine
        content = f"Template: {template_name}, Context: {context}"
        return HttpResponse(content, content_type=self.content_type)


class RedirectView(View):
    """A view that redirects to another URL."""
    
    url: Optional[str] = None
    permanent: bool = False
    
    def get_redirect_url(self, *args, **kwargs) -> Optional[str]:
        """Get the URL to redirect to."""
        if self.url:
            return self.url % kwargs
        return None
    
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET requests with redirect."""
        url = self.get_redirect_url(*args, **kwargs)
        if url:
            status = 301 if self.permanent else 302
            response = HttpResponse(status=status)
            response['Location'] = url
            return response
        else:
            # No URL to redirect to
            return HttpResponse("Gone", status=410)
    
    def head(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle HEAD requests with redirect."""
        return self.get(request, *args, **kwargs)
    
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle POST requests with redirect."""
        return self.get(request, *args, **kwargs)
    
    def options(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle OPTIONS requests with redirect."""
        return self.get(request, *args, **kwargs)
    
    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle DELETE requests with redirect."""
        return self.get(request, *args, **kwargs)
    
    def put(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle PUT requests with redirect."""
        return self.get(request, *args, **kwargs)
    
    def patch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle PATCH requests with redirect."""
        return self.get(request, *args, **kwargs)
