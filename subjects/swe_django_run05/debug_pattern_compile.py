#!/usr/bin/env python3
"""Debug pattern compilation."""

from djangoframework.urls import URLPattern

def int_view(request, user_id):
    return f"User ID: {user_id}"

# Test integer parameter pattern
pattern = URLPattern('user/<int:user_id>/', int_view)
print(f"Pattern: '{pattern.pattern}'")
print(f"Regex: {pattern.regex.pattern}")
print(f"Param names: {pattern.param_names}")

# Test matching
test_paths = ['/user/123/', 'user/123/', '/user/123', 'user/123']
for test_path in test_paths:
    result = pattern.match(test_path)
    print(f"Match result for '{test_path}': {result}")

# Test the regex directly
import re
print(f"\nDirect regex test:")
match = pattern.regex.match('/user/123/')
print(f"Direct match: {match}")
if match:
    print(f"Groups: {match.groups()}")
    print(f"Groupdict: {match.groupdict()}")
