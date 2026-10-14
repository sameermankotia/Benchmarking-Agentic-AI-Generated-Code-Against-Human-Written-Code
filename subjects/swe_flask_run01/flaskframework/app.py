"""
Main Flask application class with WSGI compatibility.
"""

import os
import sys
import traceback
from typing import Dict, List, Callable, Optional, Any, Union

from .context import AppContext
from .request import Request
from .response import Response, make_response
from .routing import Router
from .templating import TemplateEngine


class Flask:
    """The Flask application class."""
    
    def __init__(self, import_name: str, template_folder: str = 'templates',
                 static_folder: str = 'static'):
        self.import_name = import_name
        self.template_folder = template_folder
        self.static_folder = static_folder
        
        # Initialize components
        self.router = Router()
        self.template_engine = TemplateEngine(template_folder)
        
        # Configuration
        self.config = {}
        self.debug = False
        
        # Blueprints
        self.blueprints = {}
        
        # Error handlers
        self.error_handlers = {}
        
        # Before/after request handlers
        self.before_request_funcs = []
        self.after_request_funcs = []
    
    def route(self, rule: str, methods: List[str] = None):
        """Decorator for adding routes."""
        return self.router.route(rule, methods)
    
    def add_url_rule(self, rule: str, endpoint: str = None, view_func: Callable = None,
                     methods: List[str] = None):
        """Add a URL rule to the application."""
        self.router.add_url_rule(rule, endpoint, view_func, methods)
    
    def register_blueprint(self, blueprint, **options):
        """Register a blueprint with the application."""
        blueprint.register(self, options)
        self.blueprints[blueprint.name] = blueprint
    
    def errorhandler(self, code_or_exception):
        """Decorator for registering error handlers."""
        def decorator(func):
            self.error_handlers[code_or_exception] = func
            return func
        return decorator
    
    def before_request(self, func):
        """Decorator for registering before request handlers."""
        self.before_request_funcs.append(func)
        return func
    
    def after_request(self, func):
        """Decorator for registering after request handlers."""
        self.after_request_funcs.append(func)
        return func
    
    def app_context(self):
        """Create an application context."""
        return AppContext(self)
    
    def make_response(self, rv):
        """Create a response object from various return values."""
        return make_response(rv)
    
    def handle_exception(self, e):
        """Handle an exception during request processing."""
        # Look for a specific error handler
        handler = self.error_handlers.get(type(e))
        if handler:
            return self.make_response(handler(e))
        
        # Look for HTTP error handlers
        if hasattr(e, 'code'):
            handler = self.error_handlers.get(e.code)
            if handler:
                return self.make_response(handler(e))
        
        # Default error handling
        if self.debug:
            # Return traceback in debug mode
            tb = traceback.format_exc()
            return Response(f"<pre>{tb}</pre>", status=500, mimetype='text/html')
        else:
            return Response("Internal Server Error", status=500)
    
    def dispatch_request(self, request):
        """Dispatch a request to the appropriate handler."""
        try:
            # Run before request handlers
            for func in self.before_request_funcs:
                rv = func()
                if rv is not None:
                    return self.make_response(rv)
            
            # Match the request to a route
            view_func, kwargs = self.router.match_request(request.path, request.method)
            
            if view_func is None:
                # No route found - 404
                handler = self.error_handlers.get(404)
                if handler:
                    return self.make_response(handler())
                return Response("Not Found", status=404)
            
            # Call the view function
            rv = view_func(**kwargs)
            response = self.make_response(rv)
            
            # Run after request handlers
            for func in self.after_request_funcs:
                response = func(response) or response
            
            return response
            
        except Exception as e:
            return self.handle_exception(e)
    
    def wsgi_app(self, environ, start_response):
        """WSGI application callable."""
        request = Request(environ)
        
        with AppContext(self):
            response = self.dispatch_request(request)
        
        # Start the response
        start_response(response.status, list(response.headers.items()))
        
        # Return the response body
        return [response.data]
    
    def __call__(self, environ, start_response):
        """Make the app callable as a WSGI application."""
        return self.wsgi_app(environ, start_response)
    
    def run(self, host='127.0.0.1', port=5000, debug=False, **options):
        """Run the application with the built-in development server."""
        self.debug = debug
        
        from .server import run_simple
        run_simple(host, port, self, **options)


# Convenience functions
def url_for(endpoint: str, **values):
    """Generate a URL for the given endpoint."""
    # This is a simplified implementation
    # In a full implementation, this would reverse the routing
    return f"/{endpoint}"


def redirect(location: str, code: int = 302):
    """Create a redirect response."""
    response = Response("", status=code)
    response.headers['Location'] = location
    return response


def abort(code: int, description: str = None):
    """Abort the current request with an HTTP error."""
    class HTTPException(Exception):
        def __init__(self, code, description=None):
            self.code = code
            self.description = description
    
    raise HTTPException(code, description)
