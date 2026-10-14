"""
URL routing with variable segments and HTTP method filtering.
"""

import re
from typing import Dict, List, Tuple, Callable, Optional, Any


class Rule:
    """A URL routing rule."""
    
    def __init__(self, rule: str, endpoint: str, methods: List[str] = None):
        self.rule = rule
        self.endpoint = endpoint
        self.methods = set(methods or ['GET'])
        
        # Convert Flask-style route to regex
        self.regex, self.variables = self._compile_rule(rule)
    
    def _compile_rule(self, rule: str) -> Tuple[re.Pattern, List[Tuple[str, str]]]:
        """Convert a Flask-style route pattern to a regex pattern."""
        variables = []  # List of (name, converter) tuples
        
        # Find all variable segments like <name> or <int:name>
        def replace_variable(match):
            full_match = match.group(0)
            var_spec = match.group(1)
            
            if ':' in var_spec:
                # Type converter specified (e.g., <int:id>)
                converter, name = var_spec.split(':', 1)
                variables.append((name, converter))
                
                if converter == 'int':
                    return r'(\d+)'
                elif converter == 'float':
                    return r'(\d+\.?\d*)'
                elif converter == 'path':
                    return r'([^/]+(?:/[^/]+)*)'
                else:
                    # Default to string
                    return r'([^/]+)'
            else:
                # No converter specified, default to string
                variables.append((var_spec, 'string'))
                return r'([^/]+)'
        
        # Replace variable segments
        pattern = re.sub(r'<([^>]+)>', replace_variable, rule)
        
        # Escape other regex special characters
        pattern = pattern.replace('.', r'\.')
        
        # Ensure exact match
        pattern = f'^{pattern}$'
        
        return re.compile(pattern), variables
    
    def match(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Check if this rule matches the given path and method."""
        if method not in self.methods:
            return None
        
        match = self.regex.match(path)
        if not match:
            return None
        
        # Extract variables with type conversion
        values = {}
        for i, (name, converter) in enumerate(self.variables):
            raw_value = match.group(i + 1)
            
            # Convert value based on converter type
            if converter == 'int':
                values[name] = int(raw_value)
            elif converter == 'float':
                values[name] = float(raw_value)
            else:
                values[name] = raw_value
        
        return values


class Map:
    """URL map containing routing rules."""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.endpoints: Dict[str, Callable] = {}
    
    def add(self, rule: Rule, view_func: Callable):
        """Add a routing rule."""
        self.rules.append(rule)
        self.endpoints[rule.endpoint] = view_func
        # Sort rules so more specific ones (with type converters) come first
        self._sort_rules()
    
    def _sort_rules(self):
        """Sort rules by specificity - more specific rules first."""
        def rule_specificity(rule):
            # Count non-string converters (more specific)
            non_string_converters = sum(1 for name, converter in rule.variables if converter != 'string')
            # Count total variables (fewer variables = more specific for same converter count)
            total_variables = len(rule.variables)
            # Static parts count (more static parts = more specific)
            static_parts = len([part for part in rule.rule.split('/') if not part.startswith('<')])
            
            # Return tuple for sorting: (non_string_converters desc, static_parts desc, total_variables asc)
            return (-non_string_converters, -static_parts, total_variables)
        
        self.rules.sort(key=rule_specificity)
    
    def match(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, Any]]:
        """Find a matching rule for the given path and method."""
        for rule in self.rules:
            values = rule.match(path, method)
            if values is not None:
                view_func = self.endpoints.get(rule.endpoint)
                return view_func, values
        
        return None, {}


class Router:
    """URL router for the application."""
    
    def __init__(self):
        self.url_map = Map()
    
    def add_url_rule(self, rule: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a URL rule to the router."""
        rule_obj = Rule(rule, endpoint, methods)
        self.url_map.add(rule_obj, view_func)
    
    def match(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, Any]]:
        """Match a request to a view function."""
        return self.url_map.match(path, method)
