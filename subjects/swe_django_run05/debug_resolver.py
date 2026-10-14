#!/usr/bin/env python3
"""Debug URL resolver."""

from djangoframework import path, URLResolver

def error_view(request):
    raise ValueError("Test error")

urlpatterns = [
    path('/error/', error_view),
]

resolver = URLResolver(urlpatterns)

try:
    view_func, kwargs = resolver.resolve('/error/')
    print(f"Resolved view: {view_func}")
    print(f"Kwargs: {kwargs}")
except ValueError as e:
    print(f"Resolution failed: {e}")

# Test with different paths
test_paths = ['/error/', '/error', 'error/', 'error']
for test_path in test_paths:
    try:
        view_func, kwargs = resolver.resolve(test_path)
        print(f"Path '{test_path}' resolved to: {view_func}")
    except ValueError as e:
        print(f"Path '{test_path}' failed: {e}")
