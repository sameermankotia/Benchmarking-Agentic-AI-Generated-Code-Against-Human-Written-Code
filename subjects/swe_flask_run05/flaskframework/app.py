"""
Main Flask application class with WSGI compatibility.
"""
import re
import sys
import threading
from typing import Callable, List, Optional, Dict, Any, Tuple
from urllib.parse import unquote

from .request import Request
from .response import Response
from .context import AppContext
from .templating import TemplateEngine


class Flask:
    """WSGI-compatible micro web framework."""
    
    def __init__(self, import_name: str, template_folder: str = 'templates'):
        self.import_name = import_name
        self.template_folder = template_folder
        self.template_engine = TemplateEngine(template_folder)
        
        # URL routing
        self.url_map: List[Dict[str, Any]] = []
        self.view_functions: Dict[str, Callable] = {}
        
        # Blueprints
        self.blueprints: Dict[str, Any] = {}
        
        # Error handlers
        self.error_handlers: Dict[int, Callable] = {}
        
        # Configuration
        self.config = {}
        
    def route(self, rule: str, methods: Optional[List[str]] = None):
        """Decorator for registering routes."""
        if methods is None:
            methods = ['GET']
        
        def decorator(func: Callable):
            endpoint = func.__name__
            self.add_url_rule(rule, endpoint, func, methods)
            return func
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str]):
        """Add a URL rule to the application."""
        # Convert Flask-style route to regex
        pattern = self._rule_to_regex(rule)
        
        rule_info = {
            'rule': rule,
            'pattern': pattern,
            'endpoint': endpoint,
            'methods': [m.upper() for m in methods],
            'view_func': view_func
        }
        
        self.url_map.append(rule_info)
        self.view_functions[endpoint] = view_func
    
    def _rule_to_regex(self, rule: str) -> re.Pattern:
        """Convert Flask-style URL rule to regex pattern."""
        # First escape special regex characters (but not < and >)
        pattern = rule
        pattern = re.escape(pattern)
        
        # Now unescape < and > for our variable processing
        pattern = pattern.replace('\\<', '<').replace('\\>', '>')
        
        # Replace variable segments
        var_pattern = r'<(?:(\w+):)?(\w+)>'
        
        def replace_var(match):
            type_name = match.group(1) or 'string'
            var_name = match.group(2)
            
            if type_name == 'int':
                return f'(?P<{var_name}>\\d+)'
            elif type_name == 'float':
                return f'(?P<{var_name}>\\d+\\.\\d+)'
            elif type_name == 'path':
                return f'(?P<{var_name}>[^/]+(?:/[^/]+)*)'
            else:  # string (default)
                return f'(?P<{var_name}>[^/]+)'
        
        pattern = re.sub(var_pattern, replace_var, pattern)
        
        # Ensure exact match
        pattern = f'^{pattern}$'
        
        return re.compile(pattern)
    
    def register_blueprint(self, blueprint, **options):
        """Register a blueprint with the application."""
        self.blueprints[blueprint.name] = blueprint
        blueprint.register(self, options)
    
    def match_request(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, Any]]:
        """Match a request to a view function."""
        # Sort rules by specificity (more specific patterns first)
        # Rules with type constraints (int, float) are more specific than string rules
        sorted_rules = sorted(self.url_map, key=lambda r: self._rule_specificity(r['rule']), reverse=True)
        
        for rule_info in sorted_rules:
            if method.upper() not in rule_info['methods']:
                continue
                
            match = rule_info['pattern'].match(path)
            if match:
                return rule_info['view_func'], match.groupdict()
        
        return None, {}
    
    def _rule_specificity(self, rule: str) -> int:
        """Calculate rule specificity for sorting. Higher values = more specific."""
        specificity = 0
        
        # Count static segments (higher specificity)
        static_segments = len([seg for seg in rule.split('/') if seg and not seg.startswith('<')])
        specificity += static_segments * 100
        
        # Count typed variables (medium specificity)
        typed_vars = len(re.findall(r'<\w+:\w+>', rule))
        specificity += typed_vars * 10
        
        # Count untyped variables (lower specificity)
        untyped_vars = len(re.findall(r'<\w+>', rule)) - typed_vars
        specificity += untyped_vars * 1
        
        return specificity
    
    def dispatch_request(self, request: Request) -> Response:
        """Dispatch request to appropriate view function."""
        view_func, url_args = self.match_request(request.path, request.method)
        
        if view_func is None:
            return self.handle_404()
        
        try:
            # Call view function with URL arguments
            if url_args:
                result = view_func(**url_args)
            else:
                result = view_func()
            
            # Convert result to Response object
            return self._convert_to_response(result)
                
        except Exception as e:
            return self.handle_500(e)
    
    def handle_404(self) -> Response:
        """Handle 404 Not Found errors."""
        if 404 in self.error_handlers:
            result = self.error_handlers[404]()
            return self._convert_to_response(result)
        return Response("Not Found", status=404)
    
    def handle_500(self, error: Exception) -> Response:
        """Handle 500 Internal Server Error."""
        if 500 in self.error_handlers:
            result = self.error_handlers[500](error)
            return self._convert_to_response(result)
        return Response("Internal Server Error", status=500)
    
    def _convert_to_response(self, result) -> Response:
        """Convert view function result to Response object."""
        if isinstance(result, Response):
            return result
        elif isinstance(result, str):
            return Response(result)
        elif isinstance(result, tuple):
            if len(result) == 2:
                body, status = result
                return Response(body, status=status)
            elif len(result) == 3:
                body, status, headers = result
                return Response(body, status=status, headers=headers)
        else:
            return Response(str(result))
    
    def errorhandler(self, code: int):
        """Decorator for registering error handlers."""
        def decorator(func: Callable):
            self.error_handlers[code] = func
            return func
        return decorator
    
    def app_context(self):
        """Create an application context."""
        return AppContext(self)
    
    def wsgi_app(self, environ, start_response):
        """WSGI application callable."""
        with self.app_context():
            request = Request(environ)
            response = self.dispatch_request(request)
            
            status = response.status
            headers = response.get_wsgi_headers()
            
            start_response(status, headers)
            return iter(response)
    
    def __call__(self, environ, start_response):
        """Make the Flask app callable for WSGI."""
        return self.wsgi_app(environ, start_response)
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the development server."""
        from wsgiref.simple_server import make_server
        
        print(f" * Running on http://{host}:{port}/")
        if debug:
            print(" * Debug mode: on")
        
        server = make_server(host, port, self)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n * Shutting down server...")