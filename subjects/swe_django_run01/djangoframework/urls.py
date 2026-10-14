"""
URL routing and pattern matching for Django-style framework.
"""

import re
from .converters import DEFAULT_CONVERTERS
from .response import HttpResponseNotFound


class ResolverMatch:
    """Represents a successful URL resolution."""
    
    def __init__(self, func, args, kwargs, url_name=None, app_names=None, namespaces=None):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.url_name = url_name
        self.app_names = app_names or []
        self.namespaces = namespaces or []


class URLPattern:
    """A single URL pattern."""
    
    def __init__(self, pattern, callback, kwargs=None, name=None):
        self.pattern = pattern
        self.callback = callback
        self.default_kwargs = kwargs or {}
        self.name = name
        
        # Compile the pattern
        if hasattr(pattern, 'regex'):
            # It's already a compiled pattern
            self.regex = pattern.regex
            self._converters = getattr(pattern, 'converters', {})
        else:
            # It's a string pattern, compile it
            self.regex, self._converters = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern):
        """Compile a path pattern with typed converters."""
        converters = {}
        
        # Find all <type:name> or <name> segments
        def replace_converter(match):
            full_match = match.group(0)
            converter_type = match.group(1) or 'str'
            name = match.group(2)
            
            if converter_type not in DEFAULT_CONVERTERS:
                raise ValueError(f"Unknown converter type: {converter_type}")
            
            converter = DEFAULT_CONVERTERS[converter_type]
            converters[name] = converter
            
            # Return named group with converter regex
            return f'(?P<{name}>{converter.regex})'
        
        # Pattern for <type:name> or <name>
        converter_pattern = r'<(?:([^:>]+):)?([^>]+)>'
        regex_pattern = re.sub(converter_pattern, replace_converter, pattern)
        
        # Ensure pattern matches from start to end
        if not regex_pattern.startswith('^'):
            regex_pattern = '^' + regex_pattern
        if not regex_pattern.endswith('$'):
            regex_pattern = regex_pattern + '$'
        
        return re.compile(regex_pattern), converters
    
    def resolve(self, path):
        """Try to match this pattern against the given path."""
        match = self.regex.match(path)
        if match:
            kwargs = match.groupdict()
            
            # Convert matched values using converters
            for name, value in kwargs.items():
                if name in self._converters:
                    kwargs[name] = self._converters[name].to_python(value)
            
            # Add default kwargs
            kwargs.update(self.default_kwargs)
            
            return ResolverMatch(
                func=self.callback,
                args=(),
                kwargs=kwargs,
                url_name=self.name
            )
        return None


class RegexURLPattern:
    """A regex-based URL pattern."""
    
    def __init__(self, regex, callback, kwargs=None, name=None):
        if isinstance(regex, str):
            self.regex = re.compile(regex)
        else:
            self.regex = regex
        self.callback = callback
        self.default_kwargs = kwargs or {}
        self.name = name
    
    def resolve(self, path):
        """Try to match this pattern against the given path."""
        match = self.regex.match(path)
        if match:
            kwargs = match.groupdict()
            args = match.groups()
            
            # If we have named groups, use kwargs; otherwise use args
            if kwargs:
                kwargs.update(self.default_kwargs)
                return ResolverMatch(
                    func=self.callback,
                    args=(),
                    kwargs=kwargs,
                    url_name=self.name
                )
            else:
                return ResolverMatch(
                    func=self.callback,
                    args=args,
                    kwargs=self.default_kwargs,
                    url_name=self.name
                )
        return None


class URLResolver:
    """Resolves URLs against a list of patterns."""
    
    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns
    
    def resolve(self, path):
        """Resolve a path against the URL patterns."""
        for pattern in self.urlpatterns:
            match = pattern.resolve(path)
            if match:
                return match
        return None


def path(route, view, kwargs=None, name=None):
    """Create a URL pattern with typed path converters."""
    return URLPattern(route, view, kwargs, name)


def re_path(regex, view, kwargs=None, name=None):
    """Create a regex-based URL pattern."""
    return RegexURLPattern(regex, view, kwargs, name)
