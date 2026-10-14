# Django Framework

A Django-like WSGI-compatible URL routing and view dispatching framework for Python 3.11+.

## Features

This framework implements the core Django URL routing and view dispatching functionality:

1. **URL Resolution**: Supports literal paths, variable segments with typed converters (int, str, slug, uuid, path), and regular expression patterns with named groups
2. **Request Object**: Encapsulates HTTP method, path, headers, query string, and body data
3. **View Dispatch**: Routes requests to matching views, returns 404 for unmatched patterns
4. **Response Handling**: Provides response objects with status codes, headers, and body content
5. **Class-Based Views**: Dispatches requests to HTTP verb methods, handles 405 responses with Allow headers, serves HEAD from GET implementations

## Installation

```bash
pip install -e .
```

## Quick Start

### Basic Usage

```python
from djangoframework import path, HttpResponse, WSGIApplication

def hello_world(request):
    return HttpResponse("Hello, World!")

def hello_name(request, name):
    return HttpResponse(f"Hello, {name}!")

urlpatterns = [
    path('', hello_world),
    path('hello/<str:name>/', hello_name),
]

application = WSGIApplication(urlpatterns)
```

### URL Patterns

The framework supports several types of URL patterns:

```python
from djangoframework import path, re_path

urlpatterns = [
    # Literal path
    path('about/', about_view),
    
    # String parameter (default)
    path('user/<str:username>/', user_profile),
    
    # Integer parameter
    path('article/<int:id>/', article_detail),
    
    # Slug parameter
    path('category/<slug:category>/', category_view),
    
    # UUID parameter
    path('object/<uuid:obj_id>/', object_view),
    
    # Path parameter (includes slashes)
    path('files/<path:filepath>/', file_view),
    
    # Regular expression pattern
    re_path(r'^archive/(?P<year>[0-9]{4})/$', archive_view),
]
```

### Class-Based Views

```python
from djangoframework import View, HttpResponse

class MyView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("GET request")
    
    def post(self, request, *args, **kwargs):
        return HttpResponse("POST request")

urlpatterns = [
    path('my-view/', MyView.as_view()),
]
```

### WSGI Integration

```python
# wsgi.py
from djangoframework import WSGIApplication, path, HttpResponse

def home(request):
    return HttpResponse("Welcome to Django Framework!")

urlpatterns = [
    path('', home),
]

application = WSGIApplication(urlpatterns)

# For use with WSGI servers like gunicorn:
# gunicorn wsgi:application
```

## API Reference

### URL Patterns

- `path(route, view, name=None)`: Create a URL pattern with parameter conversion
- `re_path(regex, view, name=None)`: Create a URL pattern using regular expressions
- `include(patterns)`: Include a list of URL patterns

### HTTP Objects

- `HttpRequest`: Encapsulates HTTP request data
- `HttpResponse(content='', status=200, content_type='text/html; charset=utf-8')`: HTTP response object
- `HttpResponseNotFound(content='Not Found')`: 404 response
- `HttpResponseNotAllowed(allowed_methods, content='Method Not Allowed')`: 405 response

### Views

- `View`: Base class for class-based views with automatic HTTP method dispatch

### WSGI

- `WSGIApplication(urlpatterns)`: WSGI-compatible application
- `get_wsgi_application(urlpatterns)`: Factory function for creating WSGI applications

## URL Converters

The framework includes built-in converters for URL parameters:

- `str`: String (default) - matches any text except slashes
- `int`: Integer - matches positive integers
- `slug`: Slug - matches letters, numbers, hyphens, and underscores
- `uuid`: UUID - matches UUID format strings
- `path`: Path - matches any text including slashes

## HTTP Method Handling

Class-based views automatically handle HTTP methods:

- Dispatch requests to methods named after HTTP verbs (get, post, put, etc.)
- Return 405 Method Not Allowed for unsupported methods
- Automatically serve HEAD requests from GET implementations
- Include proper Allow headers in 405 responses

## WSGI Compliance

The framework is fully WSGI-compatible and can be used with any WSGI server:

```bash
# Using gunicorn
gunicorn myapp.wsgi:application

# Using uWSGI
uwsgi --http :8000 --wsgi-file myapp/wsgi.py --callable application

# Using Python's built-in server (development only)
python -m wsgiref.simple_server localhost 8000 myapp.wsgi:application
```

## Development

To set up for development:

```bash
git clone <repository-url>
cd djangoframework
pip install -e .[dev]
pytest
```

## License

MIT License
