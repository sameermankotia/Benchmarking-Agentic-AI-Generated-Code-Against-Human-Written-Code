"""
Blueprint-based modular applications with URL prefix inheritance.
"""
from typing import List, Callable, Optional


class Blueprint:
    """A blueprint for organizing routes and handlers."""
    
    def __init__(self, name: str, import_name: str, url_prefix: str = None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix or ''
        self.deferred_functions = []
    
    def route(self, rule: str, methods: List[str] = None):
        """Decorator to register a route with this blueprint."""
        def decorator(func: Callable):
            self.add_url_rule(rule, func.__name__, func, methods)
            return func
        return decorator
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule to this blueprint."""
        # Prepend the blueprint's URL prefix
        full_rule = self.url_prefix.rstrip('/') + rule
        if not full_rule.startswith('/'):
            full_rule = '/' + full_rule
        
        # Store the rule to be registered later when blueprint is registered with app
        self.deferred_functions.append({
            'rule': full_rule,
            'endpoint': f"{self.name}.{endpoint}",
            'view_func': view_func,
            'methods': methods
        })
    
    def register(self, app, options):
        """Register this blueprint with an application."""
        # Apply any options like url_prefix override
        url_prefix = options.get('url_prefix', self.url_prefix)
        
        for deferred in self.deferred_functions:
            rule = deferred['rule']
            
            # Apply url_prefix from registration if different from blueprint's
            if url_prefix and url_prefix != self.url_prefix:
                # Remove blueprint's prefix and add registration prefix
                if self.url_prefix and rule.startswith(self.url_prefix):
                    rule = rule[len(self.url_prefix):]
                rule = url_prefix.rstrip('/') + rule
            
            if not rule.startswith('/'):
                rule = '/' + rule
            
            app.add_url_rule(
                rule,
                deferred['endpoint'],
                deferred['view_func'],
                deferred['methods']
            )
