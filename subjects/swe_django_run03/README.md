# Django Framework

A WSGI-compatible URL routing and view dispatching layer inspired by Django, built for Python 3.11+.

## Features

This framework provides a complete Django-style URL routing and view dispatching system with the following capabilities:

### 1. URL Resolution
- **Pattern-based routing** with Django-style syntax: `<int:id>`, `<str:name>`, `<slug:slug>`, `<uuid:uuid>`, `<path:path>`
- **Regular expression patterns** for complex URL matching
- **Type converters** that automatically convert URL segments to Python types
- **Named URL patterns** for reverse URL generation

### 2. Request Object
- Encapsulates HTTP method, path, headers, query string, and body
- Automatic parsing of query parameters and form data
- WSGI environ integration
- Support for secure (HTTPS) detection

### 3. View Dispatch System
- Function-based views with automatic parameter injection
- URL pattern matching with 404 handling for unmatched routes
- Exception handling with proper HTTP error responses

### 4. Response Handling
- `HttpResponse` objects with status codes, headers, and body content
- `JsonResponse` for JSON API endpoints
- Cookie support with security options
- Proper HTTP status text generation

### 5. Class-Based Views
- Base `View` class with HTTP method dispatch
- Automatic HEAD request handling via GET methods
- 405 Method Not Allowed responses with proper `Allow` headers
- `TemplateView` and `RedirectView` implementations
- Support for view inheritance and mixins

### 6. WSGI Compliance
- Full WSGI 1.0 specification compliance
- Proper handling of WSGI environ and start_response
- Exception handling at application level
- Support for middleware integration

## Installation

```bash
pip install djangoframework
```

## Quick Start

### Basic Usage

```python
from djangoframework import path, HttpResponse, get_wsgi_application

def hello_world(request):
    return HttpResponse("Hello, World!")

def hello_name(request, name):
    return HttpResponse(f"Hello, {name}!")

urlpatterns = [
    path('', hello_world),
    path('hello/<str:name>/', hello_name),
]

application = get_wsgi_application(urlpatterns)
```

### URL Patterns

```python
from djangoframework import path, re_path

urlpatterns = [
    # Simple paths
    path('', home_view),
    path('about/', about_view),
    
    # Parameters with type conversion
    path('user/<int:user_id>/', user_detail),
    path('post/<slug:slug>/', post_detail),
    path('file/<path:filepath>/', serve_file),
    path('item/<uuid:item_id>/', item_detail),
    
    # Regular expressions
    re_path(r'^articles/(?P<year>[0-9]{4})/$', year_archive),
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

### JSON Responses

```python
from djangoframework import JsonResponse

def api_view(request):
    data = {'message': 'Hello, API!', 'status': 'success'}
    return JsonResponse(data)
```

### Running with WSGI Server

```python
# app.py
from djangoframework import path, HttpResponse, get_wsgi_application

def home(request):
    return HttpResponse("<h1>Welcome to Django Framework!</h1>")

urlpatterns = [
    path('', home),
]

application = get_wsgi_application(urlpatterns)

if __name__ == '__main__':
    # For development - use a proper WSGI server in production
    from wsgiref.simple_server import make_server
    
    server = make_server('localhost', 8000, application)
    print("Server running on http://localhost:8000/")
    server.serve_forever()
```

## API Reference

### URL Patterns

#### `path(pattern, view, name=None)`
Create a URL pattern with Django-style parameter syntax.

- `pattern`: URL pattern string with optional parameters like `<int:id>`
- `view`: View function or class-based view
- `name`: Optional name for the pattern

#### `re_path(regex, view, name=None)`
Create a URL pattern using regular expressions.

- `regex`: Regular expression pattern string
- `view`: View function or class-based view  
- `name`: Optional name for the pattern

### Type Converters

- `str`: Matches any string except path separators (default)
- `int`: Matches positive integers
- `slug`: Matches strings consisting of ASCII letters, numbers, hyphens, and underscores
- `uuid`: Matches UUID strings
- `path`: Matches strings including path separators

### Request Object

#### `HttpRequest`
- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `GET`: Query parameters dictionary
- `POST`: Form data dictionary (for form submissions)
- `META`: Request metadata and headers
- `body`: Raw request body as bytes

### Response Objects

#### `HttpResponse(content='', content_type='text/html; charset=utf-8', status=200)`
- `content`: Response content (string or bytes)
- `status_code`: HTTP status code
- `headers`: Response headers dictionary

#### `JsonResponse(data, status=200, safe=True)`
- `data`: Data to serialize as JSON
- `status`: HTTP status code
- `safe`: If False, allows non-dict objects

### Class-Based Views

#### `View`
Base class for all class-based views.

- `as_view(**kwargs)`: Class method that returns a view function
- `dispatch(request, *args, **kwargs)`: Dispatches request to appropriate method
- HTTP method handlers: `get()`, `post()`, `put()`, `patch()`, `delete()`, `head()`, `options()`

## Advanced Usage

### Custom View Classes

```python
from djangoframework import View, JsonResponse

class APIView(View):
    def dispatch(self, request, *args, **kwargs):
        # Add CORS headers
        response = super().dispatch(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class UserAPI(APIView):
    def get(self, request, user_id):
        # Fetch user data
        user_data = {'id': user_id, 'name': 'John Doe'}
        return JsonResponse(user_data)
    
    def post(self, request, user_id):
        # Update user data
        return JsonResponse({'status': 'updated'})
```

### Error Handling

```python
from djangoframework import HttpResponse

def my_view(request):
    try:
        # Your view logic here
        return HttpResponse("Success")
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)
```

### Middleware Integration

The framework is designed to work with WSGI middleware:

```python
def simple_middleware(app):
    def middleware(environ, start_response):
        # Pre-processing
        print(f"Request: {environ['PATH_INFO']}")
        
        # Call the application
        response = app(environ, start_response)
        
        # Post-processing
        return response
    
    return middleware

# Wrap your application
application = simple_middleware(get_wsgi_application(urlpatterns))
```

## Testing

The framework includes comprehensive test coverage. Run tests with:

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Compatibility

- Python 3.11+
- WSGI 1.0 compliant
- No external dependencies for core functionality
