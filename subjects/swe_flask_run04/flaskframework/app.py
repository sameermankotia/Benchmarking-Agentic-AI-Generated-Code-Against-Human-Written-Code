"""
Main Flask application class.
"""

import os
import sys
from typing import Dict, List, Callable, Optional, Any, Union, Tuple
from wsgiref.simple_server import make_server

from .context import AppContext
from .request import Request
from .response import Response, make_response
from .routing import Router
from .templating import TemplateEngine


class Flask:
    """The Flask application object."""
    
    def __init__(self, import_name: str, template_folder: str = 'templates'):
        self.import_name = import_name
        self.template_folder = template_folder
        
        # Initialize components
        self.router = Router()
        self.template_engine = TemplateEngine(template_folder)
        
        # Configuration
        self.config = {}
        
        # Error handlers
        self.error_handlers: Dict[int, Callable] = {}
        
        # Before/after request handlers
        self.before_request_funcs: List[Callable] = []
        self.after_request_funcs: List[Callable] = []
        
        # Registered blueprints
        self.blueprints: Dict[str, Any] = {}
    
    def route(self, rule: str, methods: List[str] = None, endpoint: Optional[str] = None):
        """Decorator for adding routes."""
        def decorator(f):
            endpoint_name = endpoint or f.__name__
            self.add_url_rule(rule, endpoint_name, f, methods)
            return f
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule to the application."""
        if methods is None:
            methods = ['GET']
        self.router.add_url_rule(rule, endpoint, view_func, methods)
    
    def register_blueprint(self, blueprint, **options):
        """Register a blueprint with the application."""
        blueprint.register(self, options)
        self.blueprints[blueprint.name] = blueprint
    
    def errorhandler(self, code: int):
        """Decorator for registering error handlers."""
        def decorator(f):
            self.error_handlers[code] = f
            return f
        return decorator
    
    def before_request(self, f):
        """Decorator for registering before request handlers."""
        self.before_request_funcs.append(f)
        return f
    
    def after_request(self, f):
        """Decorator for registering after request handlers."""
        self.after_request_funcs.append(f)
        return f
    
    def make_response(self, rv) -> Response:
        """Convert return value to Response object."""
        return make_response(rv)
    
    def handle_exception(self, e: Exception) -> Response:
        """Handle an exception that occurred during request processing."""
        # Check for registered error handlers
        if isinstance(e, HTTPException):
            handler = self.error_handlers.get(e.code)
            if handler:
                return self.make_response(handler(e))
            return self.make_response((str(e), e.code))
        
        # For other exceptions, return 500
        handler = self.error_handlers.get(500)
        if handler:
            return self.make_response(handler(e))
        
        return self.make_response(('Internal Server Error', 500))
    
    def dispatch_request(self, request: Request) -> Response:
        """Dispatch the request to the appropriate view function."""
        try:
            # Run before request handlers
            for func in self.before_request_funcs:
                rv = func()
                if rv is not None:
                    return self.make_response(rv)
            
            # Find matching route
            view_func, values = self.router.match(request.path, request.method)
            
            if view_func is None:
                raise HTTPException(404, 'Not Found')
            
            # Call view function with URL variables
            if values:
                response = view_func(**values)
            else:
                response = view_func()
            
            response = self.make_response(response)
            
            # Run after request handlers
            for func in self.after_request_funcs:
                response = func(response) or response
            
            return response
            
        except HTTPException as e:
            return self.handle_exception(e)
        except Exception as e:
            return self.handle_exception(e)
    
    def wsgi_app(self, environ: Dict[str, Any], start_response: Callable):
        """WSGI application callable."""
        request = Request(environ)
        
        # Create and push application context
        with AppContext(self):
            response = self.dispatch_request(request)
            
            # Start the response
            start_response(response.status, response.get_wsgi_headers())
            
            # Return response body
            return [response.data]
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable):
        """Make the app callable as a WSGI application."""
        return self.wsgi_app(environ, start_response)
    
    def run(self, host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
        """Run the application using the built-in development server."""
        print(f" * Running on http://{host}:{port}/")
        if debug:
            print(" * Debug mode: on")
        
        try:
            server = make_server(host, port, self)
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n * Shutting down...")


class HTTPException(Exception):
    """HTTP exception with status code."""
    
    def __init__(self, code: int, description: str = ''):
        self.code = code
        self.description = description
        super().__init__(description)
