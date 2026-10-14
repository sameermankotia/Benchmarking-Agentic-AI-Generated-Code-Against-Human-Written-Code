# Django Framework

A Django-like WSGI framework with URL routing and class-based views, built for Python 3.11+.

## Features

This framework provides a complete WSGI-compatible URL routing and view dispatching layer with the following capabilities:

### 1. URL Resolution
- **Literal paths**: Exact string matching for static routes
- **Variable segments with typed converters**:
  - `int`: Integer parameters (`<int:id>`)
  - `str`: String parameters (`<str:name>`) 
  - `slug`: Slug parameters (`<slug:article>`) - letters, numbers, hyphens, underscores
  - `uuid`: UUID parameters (`<uuid:token>`)
  - `path`: Path parameters (`<path:filepath>`) - includes slashes
- **Regular expression patterns**: Full regex support with named groups

### 2. Request Object
- Encapsulates HTTP method, path, headers, query string, and body
- URL segments captured from patterns are passed to views
- Query parameter parsing
- Header normalization

### 3. View Dispatch
- Function-based views with captured URL parameters
- First matching pattern's view is called
- 404 response for unmatched requests

### 4. Response Handling
- Response objects with status code, headers, and body
- JSON response support
- Proper HTTP status codes and headers

### 5. Class-Based Views
- Method dispatch based on HTTP verb (GET, POST, PUT, DELETE, etc.)
- 405 Method Not Allowed with proper `Allow` header for unsupported verbs
- HEAD requests automatically served from GET implementation
- Template and redirect view base classes

## Installation

```bash
pip install djangoframework
```

## Quick Start

### Basic Usage

```python
from djangoframework import (
    HttpRequest, HttpResponse, path, get_wsgi_application, View
)

# Function-based view
def hello_world(request):
    return HttpResponse("Hello, World!")

def hello_name(request, name):
    return HttpResponse(f"Hello, {name}!")

def user_profile(request, user_id):
    return HttpResponse(f"User profile for ID: {user_id}")

# Class-based view
class ArticleView(View):
    def get(self, request, slug):
        return HttpResponse(f"Article: {slug}")
    
    def post(self, request, slug):
        return HttpResponse(f"Updated article: {slug}")

# URL patterns
urlpatterns = [
    path('', hello_world),
    path('hello/<str:name>/', hello_name),
    path('user/<int:user_id>/', user_profile),
    path('article/<slug:slug>/', ArticleView.as_view()),
]

# Create WSGI application
application = get_wsgi_application(urlpatterns)
```

### Running with a WSGI Server

```python
# app.py
from djangoframework import path, get_wsgi_application, HttpResponse

def home(request):
    return HttpResponse("Welcome to Django Framework!")

urlpatterns = [
    path('', home),
]

application = get_wsgi_application(urlpatterns)

if __name__ == '__main__':
    # For development only - use a proper WSGI server in production
    from wsgiref.simple_server import make_server
    
    server = make_server('localhost', 8000, application)
    print("Server running on http://localhost:8000/")
    server.serve_forever()
```

### URL Pattern Examples

```python
from djangoframework import path, re_path

urlpatterns = [
    # Literal path
    path('about/', about_view),
    
    # String parameter
    path('user/<str:username>/', user_detail),
    
    # Integer parameter  
    path('post/<int:post_id>/', post_detail),
    
    # Slug parameter
    path('category/<slug:category_name>/', category_view),
    
    # UUID parameter
    path('token/<uuid:token>/', token_view),
    
    # Path parameter (includes slashes)
    path('files/<path:filepath>/', file_view),
    
    # Regular expression
    re_path(r'^archive/(?P<year>\d{4})/$', archive_view),
]
```

### Class-Based Views

```python
from djangoframework import View, HttpResponse, JsonResponse

class APIView(View):
    def get(self, request, item_id):
        return JsonResponse({'id': item_id, 'method': 'GET'})
    
    def post(self, request, item_id):
        return JsonResponse({'id': item_id, 'method': 'POST'})
    
    def delete(self, request, item_id):
        return HttpResponse(status=204)  # No Content

# Usage in URL patterns
urlpatterns = [
    path('api/item/<int:item_id>/', APIView.as_view()),
]
```

## WSGI Compliance

This framework is fully WSGI-compliant and can be deployed with any WSGI server:

- **Gunicorn**: `gunicorn app:application`
- **uWSGI**: `uwsgi --wsgi-file app.py --callable application`
- **Waitress**: `waitress-serve --port=8000 app:application`
- **mod_wsgi**: Compatible with Apache mod_wsgi

## API Reference

### Core Components

- `HttpRequest`: Request object with method, path, headers, query string, body
- `HttpResponse`: Response object with status, headers, content
- `JsonResponse`: JSON response helper
- `path()`: Create URL pattern with parameter syntax
- `re_path()`: Create URL pattern with regex
- `View`: Base class for class-based views
- `get_wsgi_application()`: Create WSGI application from URL patterns

### URL Converters

- `str`: String (default, excludes '/')
- `int`: Integer  
- `slug`: Alphanumeric + hyphens/underscores
- `uuid`: UUID format
- `path`: Any characters including '/'

### HTTP Methods

Class-based views support all standard HTTP methods:
- GET, POST, PUT, PATCH, DELETE
- HEAD (automatically handled via GET)
- OPTIONS, TRACE

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=djangoframework
```

### Code Quality

```bash
# Format code
black djangoframework/

# Lint code  
flake8 djangoframework/

# Type checking
mypy djangoframework/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
