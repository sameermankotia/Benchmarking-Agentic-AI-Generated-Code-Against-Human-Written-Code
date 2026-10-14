"""
Main Flask application class.
"""
import os
import sys
from typing import List, Callable, Dict, Any, Optional
from wsgiref.simple_server import make_server

from .request import Request
from .response import Response
from .routing import Router
from .context import AppContext, _app_ctx_stack
from .templating import TemplateEngine


class Flask:
    """A WSGI-compatible micro web framework."""
    
    def __init__(self, import_name: str, template_folder: str = 'templates'):
        self.import_name = import_name
        self.router = Router()
        self.template_engine = TemplateEngine(template_folder)
        self.config = {}
        self.blueprints = {}
        
        # Error handlers
        self.error_handlers = {}
    
    def route(self, rule: str, methods: List[str] = None):
        """Decorator to register a route."""
        def decorator(func: Callable):
            self.add_url_rule(rule, func.__name__, func, methods)
            return func
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule to the router."""
        self.router.add_rule(rule, endpoint, view_func, methods)
    
    def register_blueprint(self, blueprint, **options):
        """Register a blueprint with the application."""
        self.blueprints[blueprint.name] = blueprint
        blueprint.register(self, options)
    
    def errorhandler(self, code_or_exception):
        """Decorator to register an error handler."""
        def decorator(func):
            self.error_handlers[code_or_exception] = func
            return func
        return decorator
    
    def handle_exception(self, e):
        """Handle an exception and return appropriate response."""
        # Look for specific error handler
        for exc_class, handler in self.error_handlers.items():
            if isinstance(e, exc_class) or (isinstance(exc_class, int) and hasattr(e, 'code') and e.code == exc_class):
                return handler(e)
        
        # Default 500 error
        return Response('Internal Server Error', status=500)
    
    def wsgi_app(self, environ, start_response):
        """WSGI application callable."""
        # Create application context
        ctx = AppContext(self)
        _app_ctx_stack.push(ctx)
        
        try:
            # Create request object
            request = Request(environ)
            
            # Find matching route
            view_func, variables = self.router.match(request.path, request.method)
            
            if view_func is None:
                # No route found - 404
                response = Response('Not Found', status=404)
            else:
                try:
                    # Call view function with variables
                    result = view_func(**variables)
                    
                    # Convert result to Response object
                    if isinstance(result, Response):
                        response = result
                    elif isinstance(result, str):
                        response = Response(result)
                    elif isinstance(result, tuple):
                        # Handle (body, status) or (body, status, headers)
                        if len(result) == 2:
                            response = Response(result[0], status=result[1])
                        elif len(result) == 3:
                            response = Response(result[0], status=result[1], headers=result[2])
                        else:
                            response = Response(str(result))
                    else:
                        response = Response(str(result))
                        
                except Exception as e:
                    response = self.handle_exception(e)
            
            # Start WSGI response
            start_response(response.status, response.get_wsgi_headers())
            return [response.get_body_bytes()]
            
        finally:
            # Clean up context
            _app_ctx_stack.pop()
    
    def __call__(self, environ, start_response):
        """Make the app callable for WSGI."""
        return self.wsgi_app(environ, start_response)
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the application with built-in development server."""
        print(f" * Running on http://{host}:{port}")
        if debug:
            print(" * Debug mode: on")
        
        try:
            server = make_server(host, port, self)
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n * Shutting down...")


# Helper functions for common HTTP errors
class HTTPException(Exception):
    """Base class for HTTP exceptions."""
    def __init__(self, description=None):
        self.code = getattr(self, 'code', 500)
        self.description = description or getattr(self, 'description', 'Unknown error')


class NotFound(HTTPException):
    code = 404
    description = 'Not Found'


class BadRequest(HTTPException):
    code = 400
    description = 'Bad Request'


class MethodNotAllowed(HTTPException):
    code = 405
    description = 'Method Not Allowed'
