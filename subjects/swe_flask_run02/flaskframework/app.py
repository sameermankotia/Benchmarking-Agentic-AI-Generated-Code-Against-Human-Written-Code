"""
Main Flask application class with WSGI compatibility.
"""

import os
import sys
from typing import Dict, List, Callable, Optional, Any, Tuple
from .context import AppContext
from .request import Request
from .response import Response, make_response
from .routing import Map, Rule
from .templating import render_template, render_template_string


class Flask:
    """A WSGI-compatible micro web framework."""
    
    def __init__(self, import_name: str, template_folder: str = 'templates'):
        self.import_name = import_name
        self.template_folder = template_folder
        
        # URL routing
        self.url_map = Map()
        
        # Error handlers
        self.error_handlers: Dict[int, Callable] = {}
        
        # Before/after request handlers
        self.before_request_funcs: List[Callable] = []
        self.after_request_funcs: List[Callable] = []
        
        # Configuration
        self.config = {}
        
        # Debug mode
        self.debug = False
    
    def route(self, rule: str, **options):
        """Decorator for adding routes."""
        def decorator(f):
            endpoint = options.pop('endpoint', f.__name__)
            methods = options.pop('methods', ['GET'])
            self.add_url_rule(rule, endpoint, f, methods=methods)
            return f
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule."""
        if methods is None:
            methods = ['GET']
        
        rule_obj = Rule(rule, endpoint, methods)
        self.url_map.add(rule_obj, view_func)
    
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
    
    def register_blueprint(self, blueprint, **options):
        """Register a blueprint with the application."""
        blueprint.register(self, options)
    
    def make_response(self, rv) -> Response:
        """Convert return value to Response object."""
        return make_response(rv)
    
    def handle_exception(self, e: Exception) -> Response:
        """Handle exceptions and return error responses."""
        if isinstance(e, HTTPException):
            return self.handle_http_exception(e)
        
        # For other exceptions, return 500 error
        if 500 in self.error_handlers:
            return self.make_response(self.error_handlers[500](e))
        
        if self.debug:
            # In debug mode, show the full traceback
            import traceback
            tb = traceback.format_exc()
            return Response(f"<h1>Internal Server Error</h1><pre>{tb}</pre>", 
                          status=500, content_type='text/html')
        else:
            return Response("Internal Server Error", status=500)
    
    def handle_http_exception(self, e) -> Response:
        """Handle HTTP exceptions."""
        code = getattr(e, 'code', 500)
        if code in self.error_handlers:
            return self.make_response(self.error_handlers[code](e))
        
        return Response(str(e), status=code)
    
    def dispatch_request(self, request: Request) -> Response:
        """Dispatch the request to the appropriate view function."""
        try:
            # Run before request handlers
            for func in self.before_request_funcs:
                rv = func()
                if rv is not None:
                    return self.make_response(rv)
            
            # Find matching route
            view_func, values = self.url_map.match(request.path, request.method)
            
            if view_func is None:
                raise HTTPException("Not Found", 404)
            
            # Call view function with URL variables
            if values:
                rv = view_func(**values)
            else:
                rv = view_func()
            
            response = self.make_response(rv)
            
            # Run after request handlers
            for func in self.after_request_funcs:
                response = func(response) or response
            
            return response
            
        except HTTPException as e:
            return self.handle_http_exception(e)
        except Exception as e:
            return self.handle_exception(e)
    
    def wsgi_app(self, environ, start_response):
        """WSGI application callable."""
        request = Request(environ)
        
        with AppContext(self):
            response = self.dispatch_request(request)
        
        start_response(response.status, response.get_wsgi_headers())
        return iter(response)
    
    def __call__(self, environ, start_response):
        """Make the app callable for WSGI."""
        return self.wsgi_app(environ, start_response)
    
    def run(self, host='127.0.0.1', port=5000, debug=None):
        """Run the application with a built-in development server."""
        if debug is not None:
            self.debug = debug
        
        from wsgiref.simple_server import make_server
        
        print(f" * Running on http://{host}:{port}/")
        if self.debug:
            print(" * Debug mode: on")
        
        server = make_server(host, port, self)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n * Shutting down...")


class HTTPException(Exception):
    """Base class for HTTP exceptions."""
    
    def __init__(self, description: str, code: int = 500):
        self.description = description
        self.code = code
        super().__init__(description)
    
    def __str__(self):
        return self.description
