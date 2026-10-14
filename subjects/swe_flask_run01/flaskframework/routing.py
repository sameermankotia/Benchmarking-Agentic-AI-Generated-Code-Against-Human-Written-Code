"""
URL routing with variable segments and HTTP method filtering.
"""

import re
from typing import Dict, List, Tuple, Callable, Optional, Any


class Rule:
    """A URL rule that can match against request paths."""
    
    def __init__(self, rule: str, endpoint: str, methods: List[str] = None):
        self.rule = rule
        self.endpoint = endpoint
        self.methods = set(methods or ['GET'])
        
        # Convert Flask-style route to regex
        self.regex, self.variables = self._compile_rule(rule)
        
        # Calculate priority (higher priority = more specific)
        self.priority = self._calculate_priority(rule)
    
    def _compile_rule(self, rule: str) -> Tuple[re.Pattern, List[str]]:
        """Convert a Flask-style route pattern to a regex."""
        variables = []
        
        # Find all variable segments like <name> or <int:name>
        def replace_variable(match):
            full_match = match.group(0)
            var_spec = match.group(1)
            
            if ':' in var_spec:
                converter, name = var_spec.split(':', 1)
                if converter == 'int':
                    pattern = r'(\d+)'
                elif converter == 'float':
                    pattern = r'(\d+\.?\d*)'
                elif converter == 'path':
                    pattern = r'([^/]+(?:/[^/]+)*)'
                else:
                    pattern = r'([^/]+)'
            else:
                name = var_spec
                pattern = r'([^/]+)'
            
            variables.append(name)
            return pattern
        
        # Replace variable segments
        pattern = re.sub(r'<([^>]+)>', replace_variable, rule)
        
        # Escape other regex special characters
        pattern = pattern.replace('.', r'\.')
        
        # Ensure exact match
        pattern = f'^{pattern}$'
        
        return re.compile(pattern), variables
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Match a path against this rule and return variables."""
        match = self.regex.match(path)
        if not match:
            return None
        
        # Extract variables
        values = {}
        for i, name in enumerate(self.variables):
            value = match.group(i + 1)
            # Try to convert to appropriate type
            try:
                # Check if it's an integer
                if value.isdigit():
                    values[name] = int(value)
                # Check if it's a float
                elif '.' in value and value.replace('.', '').isdigit():
                    values[name] = float(value)
                else:
                    values[name] = value
            except ValueError:
                values[name] = value
        
        return values
    
    def _calculate_priority(self, rule: str) -> int:
        """Calculate rule priority. Higher number = higher priority (more specific)."""
        priority = 0
        
        # Static segments get higher priority than variable segments
        segments = rule.split('/')
        for segment in segments:
            if segment and not segment.startswith('<'):
                priority += 100  # Static segment
            elif segment.startswith('<') and ':' in segment:
                # Typed variable segments get higher priority than generic ones
                converter = segment.split(':')[0][1:]
                if converter in ('int', 'float'):
                    priority += 50  # Typed variable
                else:
                    priority += 25  # Other typed variable
            elif segment.startswith('<'):
                priority += 10  # Generic variable
        
        # Longer rules get slightly higher priority
        priority += len(segments)
        
        return priority


class Map:
    """URL map that holds all routing rules."""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.endpoints: Dict[str, Callable] = {}
    
    def add(self, rule: Rule):
        """Add a rule to the map."""
        self.rules.append(rule)
    
    def bind_endpoint(self, endpoint: str, view_func: Callable):
        """Bind a view function to an endpoint."""
        self.endpoints[endpoint] = view_func
    
    def match(self, path: str, method: str = 'GET') -> Tuple[Optional[Callable], Dict[str, Any]]:
        """Match a path and method against all rules."""
        # Sort rules by priority (highest first) for matching
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if method not in rule.methods:
                continue
            
            variables = rule.match(path)
            if variables is not None:
                view_func = self.endpoints.get(rule.endpoint)
                return view_func, variables
        
        return None, {}


class Router:
    """Main router class that handles URL routing."""
    
    def __init__(self):
        self.map = Map()
    
    def add_url_rule(self, rule: str, endpoint: str = None, view_func: Callable = None, 
                     methods: List[str] = None):
        """Add a URL rule to the router."""
        if endpoint is None:
            endpoint = view_func.__name__ if view_func else rule
        
        url_rule = Rule(rule, endpoint, methods)
        self.map.add(url_rule)
        
        if view_func is not None:
            self.map.bind_endpoint(endpoint, view_func)
    
    def route(self, rule: str, methods: List[str] = None):
        """Decorator for adding routes."""
        def decorator(func):
            self.add_url_rule(rule, func.__name__, func, methods)
            return func
        return decorator
    
    def match_request(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, Any]]:
        """Match a request against all rules."""
        return self.map.match(path, method)
