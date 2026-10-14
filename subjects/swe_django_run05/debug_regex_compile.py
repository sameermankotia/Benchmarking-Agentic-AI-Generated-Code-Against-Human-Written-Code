#!/usr/bin/env python3
"""Debug regex pattern compilation."""

from djangoframework.urls import URLPattern

def year_view(request, year):
    return f"Year: {year}"

# Test regex pattern
pattern = URLPattern(r'^archive/(?P<year>\d{4})/$', year_view)
print(f"Pattern: '{pattern.pattern}'")
print(f"Regex: {pattern.regex.pattern}")
print(f"Param names: {pattern.param_names}")

# Test matching
test_paths = ['/archive/2023/', 'archive/2023/', '/archive/2023', 'archive/2023']
for test_path in test_paths:
    result = pattern.match(test_path)
    print(f"Match result for '{test_path}': {result}")

# Test the regex directly
import re
print(f"\nDirect regex test:")
match = pattern.regex.match('/archive/2023/')
print(f"Direct match: {match}")
if match:
    print(f"Groups: {match.groups()}")
    print(f"Groupdict: {match.groupdict()}")
