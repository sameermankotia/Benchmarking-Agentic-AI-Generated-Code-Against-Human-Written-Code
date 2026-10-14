"""
Blueprint-based modular applications with URL prefix inheritance.
"""

from typing import List, Callable, Optional, Dict, Any
from .routing import Rule


class Blueprint:
    """A blueprint for organizing related routes and functionality."""
    
    def __init__(self, name: str, import_name: str, url_prefix: Optional[str] = None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix
        self.deferred_functions: List[Callable] = []
        
    def route(self, rule: str, **options):
        """Decorator for adding routes to the blueprint."""
        def decorator(f):
            endpoint = options.pop('endpoint', f.__name__)
            methods = options.pop('methods', ['GET'])
            
            def register_rule(app):
                # Apply URL prefix if set
                full_rule = rule
                if self.url_prefix:
                    # Remove trailing slash from prefix and leading slash from rule if both exist
                    prefix = self.url_prefix.rstrip('/')
                    rule_part = rule.lstrip('/')
                    full_rule = f"{prefix}/{rule_part}" if rule_part else prefix
                
                # Create endpoint name with blueprint prefix
                full_endpoint = f"{self.name}.{endpoint}"
                
                app.add_url_rule(full_rule, full_endpoint, f, methods=methods)
            
            self.deferred_functions.append(register_rule)
            return f
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule to the blueprint."""
        def register_rule(app):
            # Apply URL prefix if set
            full_rule = rule
            if self.url_prefix:
                prefix = self.url_prefix.rstrip('/')
                rule_part = rule.lstrip('/')
                full_rule = f"{prefix}/{rule_part}" if rule_part else prefix
            
            # Create endpoint name with blueprint prefix
            full_endpoint = f"{self.name}.{endpoint}"
            
            app.add_url_rule(full_rule, full_endpoint, view_func, methods=methods)
        
        self.deferred_functions.append(register_rule)
    
    def register(self, app, options=None):
        """Register the blueprint with an application."""
        for func in self.deferred_functions:
            func(app)
