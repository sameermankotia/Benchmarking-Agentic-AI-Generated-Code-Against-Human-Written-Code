"""URL routing and pattern matching for Django-style WSGI framework."""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Callable, Union


class Converter:
    """Base class for URL parameter converters."""
    
    regex = r'[^/]+'
    
    def to_python(self, value: str) -> Any:
        """Convert URL string to Python value."""
        return value
    
    def to_url(self, value: Any) -> str:
        """Convert Python value to URL string."""
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
    
    def __init__(self, pattern: str, view: Callable, name: Optional[str] = None):
        self.pattern = pattern
        self.view = view
        self.name = name
        self.regex, self.param_names, self.converters = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern: str) -> Tuple[re.Pattern, List[str], Dict[str, Converter]]:
        """Compile a Django-style URL pattern into a regex."""
        param_names = []
        converters = {}
        regex_parts = []
        
        i = 0
        while i < len(pattern):
            if pattern[i] == '<':
                # Find the end of the parameter
                end = pattern.find('>', i)
                if end == -1:
                    raise ValueError(f"Unclosed parameter in pattern: {pattern}")
                
                param_def = pattern[i+1:end]
                
                # Parse parameter definition
                if ':' in param_def:
                    converter_name, param_name = param_def.split(':', 1)
                else:
                    converter_name = 'str'
                    param_name = param_def
                
                if converter_name not in DEFAULT_CONVERTERS:
                    raise ValueError(f"Unknown converter: {converter_name}")
                
                converter = DEFAULT_CONVERTERS[converter_name]
                param_names.append(param_name)
                converters[param_name] = converter
                
                # Add named group to regex
                regex_parts.append(f'(?P<{param_name}>{converter.regex})')
                
                i = end + 1
            else:
                # Regular character - escape special regex chars
                char = pattern[i]
                if char in r'\.^$*+?{}[]|()':
                    regex_parts.append('\\' + char)
                else:
                    regex_parts.append(char)
                i += 1
        
        # Compile the final regex
        regex_str = '^' + ''.join(regex_parts) + '$'
        compiled_regex = re.compile(regex_str)
        
        return compiled_regex, param_names, converters
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Try to match the path against this pattern."""
        match = self.regex.match(path)
        if not match:
            return None
        
        # Convert matched groups using converters
        kwargs = {}
        for name, value in match.groupdict().items():
            converter = self.converters[name]
            kwargs[name] = converter.to_python(value)
        
        return kwargs


class RegexURLPattern:
    """URL pattern using raw regular expressions."""
    
    def __init__(self, regex: str, view: Callable, name: Optional[str] = None):
        self.regex = re.compile(regex)
        self.view = view
        self.name = name
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """Try to match the path against this regex pattern."""
        match = self.regex.match(path)
        if not match:
            return None
        
        # Return named groups as kwargs
        return match.groupdict()


def path(pattern: str, view: Callable, name: Optional[str] = None) -> URLPattern:
    """Create a URL pattern with Django-style parameter syntax."""
    return URLPattern(pattern, view, name)


def re_path(regex: str, view: Callable, name: Optional[str] = None) -> RegexURLPattern:
    """Create a URL pattern using raw regular expressions."""
    return RegexURLPattern(regex, view, name)


class URLResolver:
    """Resolves URLs against a list of patterns."""
    
    def __init__(self, patterns: List[Union[URLPattern, RegexURLPattern]]):
        self.patterns = patterns
    
    def resolve(self, path: str) -> Tuple[Callable, Dict[str, Any]]:
        """Resolve a path to a view function and kwargs."""
        for pattern in self.patterns:
            kwargs = pattern.match(path)
            if kwargs is not None:
                return pattern.view, kwargs
        
        # No pattern matched
        raise Http404(f"No URL pattern matches '{path}'")


class Http404(Exception):
    """Exception raised when no URL pattern matches."""
    pass
