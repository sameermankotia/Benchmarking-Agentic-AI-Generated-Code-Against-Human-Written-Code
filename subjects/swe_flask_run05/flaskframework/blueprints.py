"""
Blueprint-based modular applications with URL prefix inheritance.
"""
import re
from typing import Callable, List, Optional, Dict, Any


class Blueprint:
    """Blueprint for modular applications."""
    
    def __init__(self, name: str, import_name: str, url_prefix: Optional[str] = None):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix or ''
        self.deferred_functions: List[Callable] = []
        self._routes: List[Dict[str, Any]] = []
    
    def route(self, rule: str, methods: Optional[List[str]] = None):
        """Register a route with the blueprint."""
        if methods is None:
            methods = ['GET']
        
        def decorator(func: Callable):
            # Store route info for later registration with app
            route_info = {
                'rule': rule,
                'methods': methods,
                'func': func,
                'endpoint': f"{self.name}.{func.__name__}"
            }
            self._routes.append(route_info)
            return func
        return decorator
    
    def register(self, app, options):
        """Register blueprint with the application."""
        url_prefix = options.get('url_prefix', self.url_prefix)
        
        for route_info in self._routes:
            rule = route_info['rule']
            if url_prefix:
                # Combine blueprint prefix with route rule
                if rule.startswith('/'):
                    rule = url_prefix.rstrip('/') + rule
                else:
                    rule = url_prefix.rstrip('/') + '/' + rule
            
            # Register the route with the app
            app.add_url_rule(
                rule=rule,
                endpoint=route_info['endpoint'],
                view_func=route_info['func'],
                methods=route_info['methods']
            )
