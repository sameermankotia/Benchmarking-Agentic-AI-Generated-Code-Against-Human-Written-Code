"""
URL routing and pattern matching.
"""

import re
import uuid
from typing import Dict, Any, Callable, List, Optional, Union


class Converter:
    """Base class for URL parameter converters."""
    
    regex = '[^/]+'
    
    def to_python(self, value: str) -> Any:
        """Convert URL string to Python value."""
        return value
    
    def to_url(self, value: Any) -> str:
        """Convert Python value to URL string."""
        return str(value)


class StringConverter(Converter):
    """String converter (default)."""
    regex = '[^/]+'


class IntConverter(Converter):
    """Integer converter."""
    regex = r'\d+'
    
    def to_python(self, value: str) -> int:
        return int(value)


class SlugConverter(Converter):
    """Slug converter (letters, numbers, hyphens, underscores)."""
    regex = r'[-a-zA-Z0-9_]+'


class UUIDConverter(Converter):
    """UUID converter."""
    regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    
    def to_python(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)
    
    def to_url(self, value: uuid.UUID) -> str:
        return str(value)


class PathConverter(Converter):
    """Path converter (includes slashes)."""
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
    
    def __init__(self, pattern: str, view: Callable, name: Optional[str] = None):
        self.pattern = pattern
        self.view = view
        self.name = name
        self.regex = None
        self.param_names = []
        self.converters = {}
        self._compile_pattern()
    
    def _compile_pattern(self):
        """Compile the URL pattern into a regex."""
        # Handle angle bracket parameters like <int:id> or <str:name>
        param_pattern = r'<(?:(?P<converter>\w+):)?(?P<name>\w+)>'
        
        def replace_param(match):
            converter_name = match.group('converter') or 'str'
            param_name = match.group('name')
            
            if converter_name not in DEFAULT_CONVERTERS:
                raise ValueError(f"Unknown converter: {converter_name}")
            
            converter = DEFAULT_CONVERTERS[converter_name]
            self.param_names.append(param_name)
            self.converters[param_name] = converter
            
            return f'(?P<{param_name}>{converter.regex})'
        
        # Replace parameters with named groups
        regex_pattern = re.sub(param_pattern, replace_param, self.pattern)
        
        # Ensure pattern matches from start to end
        if not regex_pattern.startswith('^'):
            regex_pattern = '^' + regex_pattern
        if not regex_pattern.endswith('$'):
            regex_pattern = regex_pattern + '$'
        
        self.regex = re.compile(regex_pattern)
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Try to match the path against this pattern."""
        # Remove leading slash for matching (Django-style)
        if path.startswith('/'):
            path = path[1:]
        
        match = self.regex.match(path)
        if not match:
            return None
        
        # Convert matched parameters using their converters
        kwargs = {}
        for name, value in match.groupdict().items():
            if name in self.converters:
                kwargs[name] = self.converters[name].to_python(value)
            else:
                kwargs[name] = value
        
        return kwargs


class RegexURLPattern:
    """URL pattern using regular expressions."""
    
    def __init__(self, regex: str, view: Callable, name: Optional[str] = None):
        self.regex = re.compile(regex)
        self.view = view
        self.name = name
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Try to match the path against this regex pattern."""
        # Remove leading slash for consistency with URLPattern
        if path.startswith('/'):
            path = path[1:]
        
        match = self.regex.match(path)
        if not match:
            return None
        
        return match.groupdict()


class URLResolver:
    """Resolves URLs to views."""
    
    def __init__(self, patterns: List[Union[URLPattern, RegexURLPattern]]):
        self.patterns = patterns
    
    def resolve(self, path: str):
        """Resolve a path to a view and parameters."""
        for pattern in self.patterns:
            kwargs = pattern.match(path)
            if kwargs is not None:
                return pattern.view, kwargs
        
        # No pattern matched
        from .http import Http404
        raise Http404(f"No URL pattern matches '{path}'")


def path(route: str, view: Callable, name: Optional[str] = None) -> URLPattern:
    """Create a URL pattern with parameter conversion."""
    return URLPattern(route, view, name)


def re_path(regex: str, view: Callable, name: Optional[str] = None) -> RegexURLPattern:
    """Create a URL pattern using regular expressions."""
    return RegexURLPattern(regex, view, name)


def include(patterns: List[Union[URLPattern, RegexURLPattern]]) -> List[Union[URLPattern, RegexURLPattern]]:
    """Include a list of URL patterns."""
    return patterns
