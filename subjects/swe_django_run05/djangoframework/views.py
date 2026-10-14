"""View classes and utilities for Django-like framework."""

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
            instance = cls(**initkwargs)
            return instance.dispatch(request, *args, **kwargs)
        
        # Copy some attributes for introspection
        view.view_class = cls
        view.view_initkwargs = initkwargs
        
        return view
    
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch request to appropriate method handler."""
        method = request.method.lower()
        
        # Handle HEAD requests by delegating to GET if available
        if method == 'head' and not hasattr(self, 'head') and hasattr(self, 'get'):
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
            allowed_methods = []
            for method_name in self.http_method_names:
                if hasattr(self, method_name):
                    allowed_methods.append(method_name.upper())
            
            # Add HEAD if GET is available
            if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
                allowed_methods.append('HEAD')
            
            return HttpResponseNotAllowed(allowed_methods)
    
    def http_method_not_allowed(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle requests for unsupported HTTP methods."""
        allowed_methods = []
        for method in self.http_method_names:
            if hasattr(self, method):
                allowed_methods.append(method.upper())
        
        if 'GET' in allowed_methods and 'HEAD' not in allowed_methods:
            allowed_methods.append('HEAD')
        
        return HttpResponseNotAllowed(allowed_methods)


class TemplateView(View):
    """A view that renders a template."""
    
    template_name: Optional[str] = None
    content_type: str = 'text/html'
    
    def get_template_name(self) -> str:
        """Return the template name to use."""
        if self.template_name is None:
            raise ValueError("TemplateView requires either a 'template_name' attribute or an implementation of 'get_template_name()'")
        return self.template_name
    
    def get_context_data(self, **kwargs) -> dict:
        """Return the context data for the template."""
        return kwargs
    
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET requests."""
        context = self.get_context_data(**kwargs)
        # For now, just return a simple response with context as string
        # In a real implementation, this would render a template
        content = f"Template: {self.get_template_name()}, Context: {context}"
        return HttpResponse(content, content_type=self.content_type)


class RedirectView(View):
    """A view that redirects to another URL."""
    
    permanent = False
    url: Optional[str] = None
    pattern_name: Optional[str] = None
    query_string = False
    
    def get_redirect_url(self, *args, **kwargs) -> Optional[str]:
        """Return the URL to redirect to."""
        if self.url:
            return self.url % kwargs
        return None
    
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle GET requests with redirect."""
        url = self.get_redirect_url(*args, **kwargs)
        if url:
            status = 301 if self.permanent else 302
            response = HttpResponse(status=status)
            response.headers['Location'] = url
            return response
        else:
            return HttpResponse("No redirect URL provided", status=410)
    
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
