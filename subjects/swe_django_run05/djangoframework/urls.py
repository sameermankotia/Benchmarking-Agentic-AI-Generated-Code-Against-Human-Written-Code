"""URL routing and pattern matching for Django-like framework."""

import re
import uuid
from typing import Dict, List, Tuple, Any, Callable, Optional, Union
from .http import HttpRequest, HttpResponse


class URLResolverError(Exception):
    """Exception raised when URL resolution fails."""
    pass


class Converter:
    """Base class for URL parameter converters."""
    
    regex = r'[^/]+'
    
    def to_python(self, value: str) -> Any:
        """Convert URL parameter to Python value."""
        return value
    
    def to_url(self, value: Any) -> str:
        """Convert Python value to URL parameter."""
        return str(value)


class StringConverter(Converter):
    """Converter for string parameters."""
    regex = r'[^/]+'


class IntConverter(Converter):
    """Converter for integer parameters."""
    regex = r'\d+'
    
    def to_python(self, value: str) -> int:
        return int(value)


class SlugConverter(Converter):
    """Converter for slug parameters (letters, numbers, hyphens, underscores)."""
    regex = r'[-a-zA-Z0-9_]+'


class UUIDConverter(Converter):
    """Converter for UUID parameters."""
    regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    
    def to_python(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)
    
    def to_url(self, value: uuid.UUID) -> str:
        return str(value)


class PathConverter(Converter):
    """Converter for path parameters (includes slashes)."""
    regex = r'.+'


# Default converters
DEFAULT_CONVERTERS = {
    'str': StringConverter(),
    'int': IntConverter(),
    'slug': SlugConverter(),
    'uuid': UUIDConverter(),
    'path': PathConverter(),
}


class URLPattern:
    """Represents a URL pattern with optional parameters."""
    
    def __init__(self, pattern: str, view: Callable, name: Optional[str] = None, 
                 converters: Optional[Dict[str, Converter]] = None):
        self.pattern = pattern
        self.view = view
        self.name = name
        self.converters = converters or DEFAULT_CONVERTERS.copy()
        
        # Compile the pattern
        self.regex, self.param_names = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern: str) -> Tuple[re.Pattern, List[str]]:
        """Compile URL pattern to regex and extract parameter names."""
        param_names = []
        
        # Handle regex patterns (starting with ^)
        if pattern.startswith('^'):
            # This is a raw regex pattern
            regex_pattern = pattern
            # Extract named groups from regex
            for match in re.finditer(r'\(\?P<(\w+)>', pattern):
                param_names.append(match.group(1))
        else:
            # Handle Django-style patterns with <type:name> syntax
            # Ensure pattern starts with / for WSGI compatibility (but not for regex patterns)
            if not pattern.startswith('/'):
                pattern = '/' + pattern
            
            regex_pattern = '^'
            i = 0
            while i < len(pattern):
                if pattern[i] == '<':
                    # Find the closing >
                    end = pattern.find('>', i)
                    if end == -1:
                        raise ValueError(f"Unclosed parameter in pattern: {pattern}")
                    
                    param_spec = pattern[i+1:end]
                    if ':' in param_spec:
                        converter_name, param_name = param_spec.split(':', 1)
                    else:
                        converter_name = 'str'
                        param_name = param_spec
                    
                    if converter_name not in self.converters:
                        raise ValueError(f"Unknown converter: {converter_name}")
                    
                    converter = self.converters[converter_name]
                    regex_pattern += f'(?P<{param_name}>{converter.regex})'
                    param_names.append(param_name)
                    i = end + 1
                else:
                    # Escape special regex characters except for those we want to keep
                    char = pattern[i]
                    if char in '.^$*+?{}[]|()\\':
                        regex_pattern += '\\' + char
                    else:
                        regex_pattern += char
                    i += 1
            
            regex_pattern += '$'
        
        return re.compile(regex_pattern), param_names
    
    def match(self, path: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Match path against this pattern and return captured parameters."""
        match = self.regex.match(path)
        if not match:
            return None
        
        # Convert captured groups using appropriate converters
        kwargs = {}
        for name in self.param_names:
            value = match.group(name)
            # Find the converter for this parameter by checking the pattern
            # We need to determine which converter was used for this parameter
            converter = self.converters.get('str')  # default
            
            # Look through the original pattern to find the converter type
            param_pattern = f'<{name}>'
            typed_pattern = None
            for conv_name in self.converters.keys():
                if f'<{conv_name}:{name}>' in self.pattern:
                    typed_pattern = f'<{conv_name}:{name}>'
                    converter = self.converters[conv_name]
                    break
            
            if converter:
                kwargs[name] = converter.to_python(value)
            else:
                kwargs[name] = value
        
        return kwargs, match.groupdict()


class URLResolver:
    """Resolves URLs to views and handles URL routing."""
    
    def __init__(self, patterns: List[URLPattern]):
        self.patterns = patterns
    
    def resolve(self, path: str) -> Tuple[Callable, Dict[str, Any]]:
        """Resolve a path to a view function and captured parameters."""
        for pattern in self.patterns:
            result = pattern.match(path)
            if result is not None:
                kwargs, _ = result
                return pattern.view, kwargs
        
        # No pattern matched
        raise URLResolverError(f"No URL pattern matches '{path}'")


def path(route: str, view: Callable, name: Optional[str] = None) -> URLPattern:
    """Create a URL pattern with Django-style parameter syntax."""
    return URLPattern(route, view, name)


def re_path(route: str, view: Callable, name: Optional[str] = None) -> URLPattern:
    """Create a URL pattern with regex syntax."""
    return URLPattern(route, view, name)


def include(patterns: List[URLPattern]) -> List[URLPattern]:
    """Include a list of URL patterns."""
    return patterns
