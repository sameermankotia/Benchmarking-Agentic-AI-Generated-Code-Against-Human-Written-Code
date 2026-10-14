"""
Blueprint-based modular applications with URL prefix inheritance.
"""

from typing import List, Callable, Optional


class Blueprint:
    """A blueprint for organizing routes and handlers."""
    
    def __init__(self, name: str, import_name: str, url_prefix: str = None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix
        self.deferred_functions = []
    
    def route(self, rule: str, methods: List[str] = None):
        """Decorator for adding routes to the blueprint."""
        def decorator(func):
            self.add_url_rule(rule, func.__name__, func, methods)
            return func
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str = None, view_func: Callable = None,
                     methods: List[str] = None):
        """Add a URL rule to the blueprint."""
        if endpoint is None:
            endpoint = view_func.__name__ if view_func else rule
        
        # Store the rule for later registration with the app
        self.deferred_functions.append({
            'rule': rule,
            'endpoint': f"{self.name}.{endpoint}",
            'view_func': view_func,
            'methods': methods
        })
    
    def register(self, app, options):
        """Register the blueprint with an application."""
        url_prefix = options.get('url_prefix', self.url_prefix)
        
        for deferred in self.deferred_functions:
            rule = deferred['rule']
            
            # Apply URL prefix
            if url_prefix:
                if rule.startswith('/'):
                    rule = url_prefix.rstrip('/') + rule
                else:
                    rule = url_prefix.rstrip('/') + '/' + rule
            
            # Register with the app
            app.add_url_rule(
                rule,
                deferred['endpoint'],
                deferred['view_func'],
                deferred['methods']
            )
