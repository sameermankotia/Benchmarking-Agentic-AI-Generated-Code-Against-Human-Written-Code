# Django Framework

A WSGI-compatible URL routing and view dispatching framework inspired by Django's URL system.

## Features

This framework provides a complete WSGI-compatible implementation with the following features:

### 1. URL Resolution
- **Literal paths**: Match exact URL paths
- **Variable segments with typed converters**:
  - `int`: Integer parameters
  - `str`: String parameters (default)
  - `slug`: Slug parameters (letters, numbers, hyphens, underscores)
  - `uuid`: UUID parameters
  - `path`: Path parameters (includes slashes)
- **Regular expression patterns**: Full regex support with named groups

### 2. Request Object
- Encapsulates HTTP method, path, headers, query string, and body
- Automatically parses query parameters and form data
- Passes captured URL segments to views

### 3. View Dispatch
- Routes requests to the first matching URL pattern
- Calls views with request object and captured parameters
- Returns 404 for unmatched URLs

### 4. Response Handling
- Response objects with status code, headers, and body
- Automatic content-type handling
- WSGI-compliant response generation

### 5. Class-Based Views
- Method dispatch based on HTTP verbs (GET, POST, PUT, etc.)
- Automatic 405 responses with Allow header for unsupported methods
- HEAD requests automatically served from GET implementations

## Installation

```bash
pip install djangoframework
```

## Quick Start

### Basic Usage

```python
from djangoframework import WSGIApplication, HttpResponse, path

def hello_world(request):
    return HttpResponse("Hello, World!")

def hello_name(request, name):
    return HttpResponse(f"Hello, {name}!")

urlpatterns = [
    path('', hello_world),
    path('hello/<str:name>/', hello_name),
]

application = WSGIApplication(urlpatterns)

# Use with any WSGI server
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('localhost', 8000, application)
    print("Server running on http://localhost:8000")
    server.serve_forever()
```

### URL Patterns

```python
from djangoframework import path, re_path

urlpatterns = [
    # Literal path
    path('about/', about_view),
    
    # String parameter
    path('user/<str:username>/', user_profile),
    
    # Integer parameter
    path('article/<int:id>/', article_detail),
    
    # Slug parameter
    path('category/<slug:category>/', category_view),
    
    # UUID parameter
    path('object/<uuid:obj_id>/', object_view),
    
    # Path parameter (includes slashes)
    path('files/<path:filepath>/', file_view),
    
    # Regular expression
    re_path(r'^archive/(?P<year>[0-9]{4})/$', archive_view),
]
```

### Class-Based Views

```python
from djangoframework import View, HttpResponse

class ArticleView(View):
    def get(self, request, id):
        return HttpResponse(f"Article {id}")
    
    def post(self, request, id):
        return HttpResponse(f"Updated article {id}")

urlpatterns = [
    path('article/<int:id>/', ArticleView.as_view()),
]
```

### Request and Response

```python
def my_view(request):
    # Access request data
    method = request.method
    path = request.path
    headers = request.headers
    query_params = request.GET
    post_data = request.POST
    body = request.body
    
    # Create response
    response = HttpResponse("Hello!")
    response.headers['Custom-Header'] = 'value'
    return response
```

## API Reference

### URL Patterns

#### `path(route, view, name=None)`
Create a URL pattern with Django-style parameter syntax.

- `route`: URL pattern with `<converter:name>` syntax
- `view`: View function or class-based view
- `name`: Optional name for the pattern

#### `re_path(regex, view, name=None)`
Create a URL pattern using raw regular expressions.

- `regex`: Regular expression pattern
- `view`: View function or class-based view  
- `name`: Optional name for the pattern

### HTTP Classes

#### `HttpRequest`
Represents an HTTP request with the following attributes:
- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `headers`: Dictionary of HTTP headers
- `GET`: Parsed query parameters
- `POST`: Parsed form data (for POST requests)
- `body`: Raw request body as bytes

#### `HttpResponse`
Represents an HTTP response:
- `HttpResponse(content='', status=200, content_type='text/html; charset=utf-8')`
- `content`: Response content
- `status_code`: HTTP status code
- `headers`: Dictionary of response headers

### Views

#### `View`
Base class for class-based views:
- Dispatches requests to methods named after HTTP verbs
- Automatically handles HEAD requests via GET
- Returns 405 for unsupported methods with proper Allow header

### WSGI Application

#### `WSGIApplication(urlpatterns)`
Main WSGI application class:
- Takes a list of URL patterns
- Handles request routing and view dispatch
- Provides error handling for 404 and 500 responses

## WSGI Compliance

This framework is fully WSGI-compliant and can be used with any WSGI server:

```python
# With gunicorn
# gunicorn myapp:application

# With uWSGI  
# uwsgi --http :8000 --wsgi-file myapp.py --callable application

# With mod_wsgi (Apache)
# Configure application as WSGI entry point
```

## Testing

The framework includes comprehensive test coverage. Run tests with:

```bash
pytest
```

## License

MIT License - see LICENSE file for details.
