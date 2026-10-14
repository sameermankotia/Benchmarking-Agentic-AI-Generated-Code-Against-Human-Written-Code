"""
URL converters for typed path segments.
"""

import re
import uuid


class Converter:
    """Base converter class."""
    regex = '[^/]+'
    
    def to_python(self, value):
        """Convert URL segment to Python value."""
        return value
    
    def to_url(self, value):
        """Convert Python value to URL segment."""
        return str(value)


class StringConverter(Converter):
    """String converter (default)."""
    regex = '[^/]+'


class IntConverter(Converter):
    """Integer converter."""
    regex = r'[0-9]+'
    
    def to_python(self, value):
        return int(value)


class SlugConverter(Converter):
    """Slug converter (letters, numbers, hyphens, underscores)."""
    regex = r'[-a-zA-Z0-9_]+'


class UUIDConverter(Converter):
    """UUID converter."""
    regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    
    def to_python(self, value):
        return uuid.UUID(value)


class PathConverter(Converter):
    """Path converter (includes slashes)."""
    regex = r'.+'


# Default converters registry
DEFAULT_CONVERTERS = {
    'str': StringConverter(),
    'int': IntConverter(),
    'slug': SlugConverter(),
    'uuid': UUIDConverter(),
    'path': PathConverter(),
}
