#!/usr/bin/env python3
"""Debug URL pattern matching."""

from djangoframework.urls import URLPattern

def hello_view(request):
    return "Hello"

# Test empty path pattern
pattern = URLPattern('', hello_view)
print(f"Pattern: '{pattern.pattern}'")
print(f"Regex: {pattern.regex.pattern}")
print(f"Param names: {pattern.param_names}")

# Test matching
result = pattern.match('/')
print(f"Match result for '/': {result}")

result = pattern.match('')
print(f"Match result for '': {result}")

# Test with trailing slash
pattern2 = URLPattern('/', hello_view)
print(f"\nPattern2: '{pattern2.pattern}'")
print(f"Regex2: {pattern2.regex.pattern}")

result2 = pattern2.match('/')
print(f"Match result for '/': {result2}")
