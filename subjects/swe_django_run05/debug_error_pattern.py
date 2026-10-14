#!/usr/bin/env python3
"""Debug error pattern matching."""

from djangoframework.urls import URLPattern

def error_view(request):
    raise ValueError("Test error")

# Test error pattern
pattern = URLPattern('/error/', error_view)
print(f"Pattern: '{pattern.pattern}'")
print(f"Regex: {pattern.regex.pattern}")
print(f"Param names: {pattern.param_names}")

# Test matching
test_paths = ['/error/', '/error', 'error/', 'error']
for test_path in test_paths:
    result = pattern.match(test_path)
    print(f"Match result for '{test_path}': {result}")

# Test the regex directly
import re
print(f"\nDirect regex test:")
match = pattern.regex.match('/error/')
print(f"Direct match: {match}")
if match:
    print(f"Groups: {match.groups()}")
    print(f"Groupdict: {match.groupdict()}")
