# Django Framework

A WSGI-compatible URL routing and view dispatching layer inspired by Django, built for Python 3.11.

## Features

This framework implements the core Django URL routing and view dispatching functionality:

### 1. URL Resolution
- **Literal paths**: Exact string matching
- **Variable segments with typed converters**:
  - `int`: Integer values (`<int:id>`)
  - `str`: String values (`<str:name>` or `<name>`)
  - `slug`: Slug values (`<slug:title>`)
  - `uuid`: UUID values (`<uuid:pk>`)
  - `path`: Path values including slashes (`<path:filepath>`)
- **Regular expression patterns**: Full regex support with named groups

### 2. Request Object
- Encapsulates HTTP method, path, headers, query string, and body
- URL segments captured from patterns are passed to views
- Django-style META dictionary for headers and environment variables

### 3. View Dispatch
- Function-based views receive request and captured URL segments
- First matching pattern's view is called
- Unmatched requests return 404 Not Found

### 4. Response Handling
- Response objects carry status code, headers, and body
- Built-in support for common HTTP status codes
- WSGI-compatible response generation

### 5. Class-Based Views
- Views dispatch requests to methods named for HTTP verbs (get, post, etc.)
- Automatic 405 Method Not Allowed with proper Allow header
- HEAD requests automatically served from GET implementations
- OPTIONS requests return allowed methods

## Installation

```bash
pip install djangoframework
```

## Quick Start

```python
from djangoframework import WSGIApplication, HttpResponse, View, path

# Function-based view
def hello_world(request):
    return HttpResponse("Hello, World!")

def hello_name(request, name):
    return HttpResponse(f"Hello, {name}!")

def user_detail(request, user_id):
    return HttpResponse(f"User ID: {user_id}")

# Class-based view
class ArticleView(View):
    def get(self, request, article_id):
        return HttpResponse(f"Article {article_id}")
    
    def post(self, request, article_id):
        return HttpResponse(f"Updated article {article_id}")

# URL patterns
urlpatterns = [
    path('', hello_world),
    path('hello/<str:name>/', hello_name),
    path('user/<int:user_id>/', user_detail),
    path('article/<int:article_id>/', ArticleView.as_view()),
]

# Create WSGI application
application = WSGIApplication(urlpatterns)

# Run with any WSGI server
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('localhost', 8000, application)
    print("Server running on http://localhost:8000")
    server.serve_forever()
```

## URL Patterns

### Path Patterns

Use `path()` for simple patterns with typed converters:

```python
from djangoframework import path

urlpatterns = [
    path('articles/', article_list),
    path('articles/<int:id>/', article_detail),
    path('articles/<slug:title>/', article_by_title),
    path('files/<path:filepath>/', serve_file),
]
```

### Regex Patterns

Use `re_path()` for complex patterns with regular expressions:

```python
from djangoframework import re_path

urlpatterns = [
    re_path(r'^articles/(?P<year>[0-9]{4})/$', articles_by_year),
    re_path(r'^articles/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', articles_by_month),
]
```

## Class-Based Views

```python
from djangoframework import View, HttpResponse, HttpResponseNotAllowed

class MyView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("GET request")
    
    def post(self, request, *args, **kwargs):
        return HttpResponse("POST request")
    
    def put(self, request, *args, **kwargs):
        return HttpResponse("PUT request")

# Use in URL patterns
urlpatterns = [
    path('my-view/', MyView.as_view()),
]
```

Class-based views automatically:
- Return 405 Method Not Allowed for unsupported HTTP methods
- Include proper Allow header listing supported methods
- Handle HEAD requests using the GET method if available
- Support OPTIONS requests returning allowed methods

## Request Object

The request object provides access to:

```python
def my_view(request):
    method = request.method          # HTTP method (GET, POST, etc.)
    path = request.path              # URL path
    query_params = request.GET       # Query string parameters
    headers = request.META           # Headers and environment
    body = request.body              # Request body as bytes
    full_path = request.get_full_path()  # Path with query string
    
    return HttpResponse("OK")
```

## Response Object

Create responses with custom status codes and headers:

```python
from djangoframework import HttpResponse

def my_view(request):
    response = HttpResponse("Custom response", status=201)
    response['Custom-Header'] = 'value'
    response['Content-Type'] = 'text/plain'
    return response
```

## WSGI Compliance

This framework is fully WSGI-compatible and can be deployed with any WSGI server:

- **Development**: `wsgiref.simple_server`
- **Production**: Gunicorn, uWSGI, mod_wsgi, etc.

```python
# For Gunicorn
# gunicorn myapp:application

from djangoframework import WSGIApplication, path
from myviews import my_view

urlpatterns = [
    path('', my_view),
]

application = WSGIApplication(urlpatterns)
```

## Testing

The framework includes comprehensive tests covering all functionality:

```bash
pytest tests/
```

## Requirements

- Python 3.11+
- No external dependencies for core functionality

## License

MIT License - see LICENSE file for details.
