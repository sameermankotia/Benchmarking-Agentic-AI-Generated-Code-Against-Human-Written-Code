"""
URL routing with variable segments and HTTP method filtering.
"""

import re
from typing import Dict, List, Tuple, Callable, Optional, Any


class Rule:
    """A URL routing rule with variable segments and method filtering."""
    
    def __init__(self, rule: str, endpoint: str, methods: List[str] = None):
        self.rule = rule
        self.endpoint = endpoint
        self.methods = set(methods or ['GET'])
        
        # Convert Flask-style route to regex
        self.regex, self.variables, self.converters = self._compile_rule(rule)
    
    def _compile_rule(self, rule: str) -> Tuple[re.Pattern, List[str], Dict[str, str]]:
        """Convert a Flask-style route pattern to a regex pattern."""
        variables = []
        converters = {}
        
        # Find all variable segments like <name> or <int:name>
        def replace_variable(match):
            full_match = match.group(0)
            var_spec = match.group(1)
            
            if ':' in var_spec:
                converter, name = var_spec.split(':', 1)
                variables.append(name)
                converters[name] = converter
                
                # Different converters
                if converter == 'int':
                    return r'(\d+)'
                elif converter == 'float':
                    return r'(\d+\.?\d*)'
                elif converter == 'path':
                    return r'([^/]+(?:/[^/]+)*)'
                else:  # string (default)
                    return r'([^/]+)'
            else:
                # No converter specified, default to string
                variables.append(var_spec)
                converters[var_spec] = 'string'
                return r'([^/]+)'
        
        # Replace variable segments
        pattern = re.sub(r'<([^>]+)>', replace_variable, rule)
        
        # Escape other regex special characters
        pattern = pattern.replace('.', r'\.')
        
        # Ensure exact match
        pattern = f'^{pattern}$'
        
        return re.compile(pattern), variables, converters
    
    def match(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Check if this rule matches the given path and method."""
        if method not in self.methods:
            return None
        
        match = self.regex.match(path)
        if not match:
            return None
        
        # Extract variables and convert to appropriate types
        values = {}
        for i, name in enumerate(self.variables):
            value = match.group(i + 1)
            converter = self.converters.get(name, 'string')
            
            # Convert to appropriate type
            if converter == 'int':
                try:
                    values[name] = int(value)
                except ValueError:
                    return None  # Invalid integer
            elif converter == 'float':
                try:
                    values[name] = float(value)
                except ValueError:
                    return None  # Invalid float
            else:  # string or path
                values[name] = value
        
        return values


class Map:
    """A collection of URL rules."""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.endpoints: Dict[str, Callable] = {}
    
    def add(self, rule: Rule, view_func: Callable):
        """Add a rule and its associated view function."""
        self.rules.append(rule)
        self.endpoints[rule.endpoint] = view_func
        # Sort rules by specificity (more specific patterns first)
        self._sort_rules()
    
    def match(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, Any]]:
        """Find a matching rule and return the view function and variables."""
        for rule in self.rules:
            values = rule.match(path, method)
            if values is not None:
                return self.endpoints[rule.endpoint], values
        
        return None, {}
    
    def _sort_rules(self):
        """Sort rules by specificity - more specific patterns first."""
        def rule_specificity(rule):
            # Count the number of specific converters (int, float, path)
            specific_converters = 0
            generic_converters = 0
            
            # Count static parts vs variable parts
            static_parts = len(rule.rule.split('/')) - len(rule.variables)
            
            for var in rule.variables:
                # Check if this variable has a specific converter
                if '<int:' in rule.rule or '<float:' in rule.rule or '<path:' in rule.rule:
                    specific_converters += 1
                else:
                    generic_converters += 1
            
            # Rules with more static parts and specific converters come first
            return (-static_parts, -specific_converters, generic_converters)
        
        self.rules.sort(key=rule_specificity)
    
    def iter_rules(self):
        """Iterate over all rules."""
        return iter(self.rules)
