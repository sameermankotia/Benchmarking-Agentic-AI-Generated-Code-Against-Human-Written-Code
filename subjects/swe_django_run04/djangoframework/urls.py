"""
URL routing system with pattern matching and converters.
"""
import re
import uuid
from .http import Http404


class Converter:
    """Base class for URL parameter converters."""
    regex = '[^/]+'
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return str(value)


class StringConverter(Converter):
    """Converter for string parameters."""
    regex = '[^/]+'


class IntConverter(Converter):
    """Converter for integer parameters."""
    regex = r'[0-9]+'
    
    def to_python(self, value):
        return int(value)


class SlugConverter(Converter):
    """Converter for slug parameters (letters, numbers, hyphens, underscores)."""
    regex = r'[-a-zA-Z0-9_]+'


class UUIDConverter(Converter):
    """Converter for UUID parameters."""
    regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    
    def to_python(self, value):
        return uuid.UUID(value)


class PathConverter(Converter):
    """Converter for path parameters (includes slashes)."""
    regex = r'.+'


# Registry of available converters
DEFAULT_CONVERTERS = {
    'str': StringConverter(),
    'int': IntConverter(),
    'slug': SlugConverter(),
    'uuid': UUIDConverter(),
    'path': PathConverter(),
}


class URLPattern:
    """
    A URL pattern that can match against a path and extract parameters.
    """
    
    def __init__(self, pattern, view, name=None, converters=None):
        self.pattern = pattern
        self.view = view
        self.name = name
        self.converters = converters or DEFAULT_CONVERTERS.copy()
        
        # Compile the pattern into a regex
        self._compile_pattern()
    
    def _compile_pattern(self):
        """Convert Django-style URL pattern to regex."""
        # Handle angle bracket parameters like <int:id>
        param_pattern = r'<(?:(\w+):)?(\w+)>'
        
        def replace_param(match):
            converter_name = match.group(1) or 'str'
            param_name = match.group(2)
            
            if converter_name not in self.converters:
                raise ValueError(f"Unknown converter: {converter_name}")
            
            converter = self.converters[converter_name]
            return f'(?P<{param_name}>{converter.regex})'
        
        # Replace parameters with named groups
        regex_pattern = re.sub(param_pattern, replace_param, self.pattern)
        
        # Ensure pattern matches from start to end
        if not regex_pattern.startswith('^'):
            regex_pattern = '^' + regex_pattern
        if not regex_pattern.endswith('$'):
            regex_pattern = regex_pattern + '$'
        
        self.regex = re.compile(regex_pattern)
        
        # Extract parameter info for conversion
        self.param_converters = {}
        for match in re.finditer(param_pattern, self.pattern):
            converter_name = match.group(1) or 'str'
            param_name = match.group(2)
            self.param_converters[param_name] = self.converters[converter_name]
    
    def match(self, path):
        """
        Try to match the path against this pattern.
        Returns (view, kwargs) if match, None otherwise.
        """
        match = self.regex.match(path)
        if not match:
            return None
        
        # Convert matched parameters using their converters
        kwargs = {}
        for name, value in match.groupdict().items():
            converter = self.param_converters.get(name, self.converters['str'])
            kwargs[name] = converter.to_python(value)
        
        return self.view, kwargs


class RegexURLPattern:
    """
    A URL pattern using raw regular expressions.
    """
    
    def __init__(self, regex, view, name=None):
        self.regex = re.compile(regex)
        self.view = view
        self.name = name
    
    def match(self, path):
        """
        Try to match the path against this regex pattern.
        Returns (view, kwargs) if match, None otherwise.
        """
        match = self.regex.match(path)
        if not match:
            return None
        
        # Use named groups as kwargs
        kwargs = match.groupdict()
        return self.view, kwargs


class URLResolver:
    """
    Resolves URLs by trying patterns in order until one matches.
    """
    
    def __init__(self, patterns):
        self.patterns = patterns
    
    def resolve(self, path):
        """
        Resolve a path to a view and kwargs.
        Raises Http404 if no pattern matches.
        """
        for pattern in self.patterns:
            result = pattern.match(path)
            if result:
                return result
        
        raise Http404(f"No URL pattern matches '{path}'")


def path(route, view, name=None):
    """
    Create a URL pattern with Django-style parameter syntax.
    """
    return URLPattern(route, view, name)


def re_path(regex, view, name=None):
    """
    Create a URL pattern using raw regular expressions.
    """
    return RegexURLPattern(regex, view, name)
