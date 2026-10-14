"""
Blueprint-based modular applications with URL prefix inheritance.
"""

from typing import List, Callable, Optional, Dict, Any


class Blueprint:
    """A blueprint for organizing routes and handlers."""
    
    def __init__(self, name: str, import_name: str, url_prefix: Optional[str] = None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix
        
        # Store deferred functions to be registered with the app
        self._deferred_functions: List[Callable] = []
    
    def route(self, rule: str, methods: List[str] = None, endpoint: Optional[str] = None):
        """Decorator for adding routes to the blueprint."""
        def decorator(f):
            # Create endpoint name if not provided
            if endpoint is None:
                endpoint_name = f.__name__
            else:
                endpoint_name = endpoint
            
            # Store the registration function to be called later
            def register_func(app):
                # Apply URL prefix if set
                full_rule = rule
                if self.url_prefix:
                    full_rule = self.url_prefix.rstrip('/') + '/' + rule.lstrip('/')
                
                # Create full endpoint name with blueprint name
                full_endpoint = f"{self.name}.{endpoint_name}"
                
                app.add_url_rule(full_rule, full_endpoint, f, methods)
            
            self._deferred_functions.append(register_func)
            return f
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule to the blueprint."""
        def register_func(app):
            # Apply URL prefix if set
            full_rule = rule
            if self.url_prefix:
                full_rule = self.url_prefix.rstrip('/') + '/' + rule.lstrip('/')
            
            # Create full endpoint name with blueprint name
            full_endpoint = f"{self.name}.{endpoint}"
            
            app.add_url_rule(full_rule, full_endpoint, view_func, methods)
        
        self._deferred_functions.append(register_func)
    
    def register(self, app, options: Optional[Dict[str, Any]] = None):
        """Register the blueprint with an application."""
        options = options or {}
        
        # Override URL prefix if provided in options
        url_prefix = options.get('url_prefix', self.url_prefix)
        
        # Temporarily set the URL prefix for registration
        original_prefix = self.url_prefix
        self.url_prefix = url_prefix
        
        try:
            # Execute all deferred registration functions
            for func in self._deferred_functions:
                func(app)
        finally:
            # Restore original prefix
            self.url_prefix = original_prefix
