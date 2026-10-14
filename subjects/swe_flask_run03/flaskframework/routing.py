"""
URL routing with variable segments and HTTP method filtering.
"""
import re
from typing import Dict, List, Tuple, Callable, Optional


class Rule:
    """A URL routing rule."""
    
    def __init__(self, pattern: str, endpoint: str, methods: List[str] = None):
        self.pattern = pattern
        self.endpoint = endpoint
        self.methods = methods or ['GET']
        self.regex, self.variables = self._compile_pattern(pattern)
        self.priority = self._calculate_priority(pattern)
    
    def _calculate_priority(self, pattern: str) -> int:
        """Calculate rule priority. Higher priority = more specific."""
        priority = 0
        
        # Static segments have higher priority than variable segments
        segments = pattern.split('/')
        for segment in segments:
            if segment and not segment.startswith('<'):
                priority += 10  # Static segment
            elif segment.startswith('<') and ':' in segment:
                priority += 5   # Typed variable segment
            elif segment.startswith('<'):
                priority += 1   # Generic variable segment
        
        return priority
    
    def _compile_pattern(self, pattern: str) -> Tuple[re.Pattern, List[str]]:
        """Compile URL pattern to regex and extract variable names."""
        variables = []
        
        # Find all variable segments like <name> or <int:name>
        def replace_variable(match):
            full_match = match.group(0)
            var_spec = match.group(1)
            
            if ':' in var_spec:
                converter, name = var_spec.split(':', 1)
                variables.append(name)
                
                # Define converters
                if converter == 'int':
                    return r'(\d+)'
                elif converter == 'float':
                    return r'(\d+\.\d+)'
                elif converter == 'path':
                    return r'([^/]+(?:/[^/]+)*)'
                else:
                    return r'([^/]+)'
            else:
                variables.append(var_spec)
                return r'([^/]+)'
        
        # Replace variable segments with regex groups
        regex_pattern = re.sub(r'<([^>]+)>', replace_variable, pattern)
        
        # Ensure exact match
        regex_pattern = f'^{regex_pattern}$'
        
        return re.compile(regex_pattern), variables
    
    def match(self, path: str, method: str) -> Optional[Dict[str, str]]:
        """Check if this rule matches the given path and method."""
        if method not in self.methods:
            return None
        
        match = self.regex.match(path)
        if not match:
            return None
        
        # Extract variables
        values = {}
        for i, name in enumerate(self.variables):
            values[name] = match.group(i + 1)
        
        return values


class Router:
    """URL router that manages routing rules."""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.endpoints: Dict[str, Callable] = {}
    
    def add_rule(self, pattern: str, endpoint: str, view_func: Callable, methods: List[str] = None):
        """Add a routing rule."""
        rule = Rule(pattern, endpoint, methods)
        self.rules.append(rule)
        self.endpoints[endpoint] = view_func
    
    def match(self, path: str, method: str) -> Tuple[Optional[Callable], Dict[str, str]]:
        """Find a matching rule for the given path and method."""
        for rule in self.rules:
            variables = rule.match(path, method)
            if variables is not None:
                view_func = self.endpoints.get(rule.endpoint)
                return view_func, variables
        
        return None, {}
