# Flask Framework

A WSGI-compatible micro web framework built in Python 3.11 that provides essential web development features with a simple, intuitive API.

## Features

1. **URL Routing with Variable Segments and HTTP Method Filtering**
   - Support for dynamic URL segments like `/user/<int:id>`
   - HTTP method filtering (GET, POST, PUT, DELETE, etc.)
   - Type converters for URL parameters (int, float, path, string)

2. **Request Object**
   - Encapsulates HTTP method, path, headers, query string, and body
   - Easy access to form data and query parameters
   - Automatic parsing of request data

3. **Response Object**
   - Configurable status codes, headers, and body content
   - Support for different content types
   - WSGI-compatible response handling

4. **Jinja2 Template Rendering**
   - Integrated template engine with application context
   - Support for template inheritance and includes
   - Automatic HTML escaping for security

5. **Application Context Management**
   - Thread-local storage for `current_app` and `g` objects
   - Context-aware request handling
   - Safe concurrent request processing

6. **Blueprint-based Modular Applications**
   - Organize routes and handlers into reusable blueprints
   - URL prefix inheritance for blueprint registration
   - Modular application architecture

## Installation

```bash
pip install -e .
```

## Quick Start

### Basic Application

```python
from flaskframework import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/user/<name>')
def user_profile(name):
    return f'Hello, {name}!'

@app.route('/user/<int:id>')
def user_by_id(id):
    return f'User ID: {id}'

if __name__ == '__main__':
    app.run(debug=True)
```

### Using Templates

Create a `templates/` directory and add `hello.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Hello {{ name }}</title>
</head>
<body>
    <h1>Hello, {{ name }}!</h1>
</body>
</html>
```

```python
from flaskframework import Flask, render_template

app = Flask(__name__)

@app.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)

if __name__ == '__main__':
    app.run()
```

### Using Blueprints

```python
from flaskframework import Flask, Blueprint

# Create a blueprint
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    return {'users': ['alice', 'bob']}

@api.route('/users/<int:id>')
def get_user(id):
    return {'user_id': id}

# Create the main app
app = Flask(__name__)
app.register_blueprint(api)

@app.route('/')
def index():
    return 'Main application'

if __name__ == '__main__':
    app.run()
```

### Application Context

```python
from flaskframework import Flask, current_app, g

app = Flask(__name__)

@app.before_request
def before_request():
    g.user = 'anonymous'

@app.route('/context')
def show_context():
    return f'App: {current_app.import_name}, User: {g.user}'

if __name__ == '__main__':
    app.run()
```

## API Reference

### Flask Application

#### `Flask(import_name, template_folder='templates')`

Create a new Flask application.

- `import_name`: The name of the application package
- `template_folder`: Directory containing Jinja2 templates

#### Methods

- `route(rule, methods=None, endpoint=None)`: Decorator for adding routes
- `add_url_rule(rule, endpoint, view_func, methods=None)`: Add URL rule programmatically
- `register_blueprint(blueprint, **options)`: Register a blueprint
- `errorhandler(code)`: Decorator for error handlers
- `before_request(f)`: Decorator for before-request handlers
- `after_request(f)`: Decorator for after-request handlers
- `run(host='127.0.0.1', port=5000, debug=False)`: Run development server

### Blueprint

#### `Blueprint(name, import_name, url_prefix=None)`

Create a new blueprint for modular applications.

- `name`: Blueprint name
- `import_name`: Import name of the blueprint package
- `url_prefix`: URL prefix for all blueprint routes

#### Methods

- `route(rule, methods=None, endpoint=None)`: Add route to blueprint
- `add_url_rule(rule, endpoint, view_func, methods=None)`: Add URL rule to blueprint

### Request Object

Available as the current request in view functions.

#### Properties

- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `headers`: Request headers dictionary
- `query_string`: Raw query string
- `args`: Parsed query parameters
- `body`: Request body as bytes
- `data`: Request body as string
- `form`: Parsed form data (for POST requests)

### Response Object

#### `Response(response='', status=200, headers=None, mimetype='text/html')`

Create an HTTP response.

- `response`: Response body (string, bytes, or iterator)
- `status`: HTTP status code
- `headers`: Response headers dictionary
- `mimetype`: Content type

### Context Objects

- `current_app`: Proxy to the current Flask application
- `g`: Application context global object for storing data during a request

### Template Functions

- `render_template(template_name, **context)`: Render a Jinja2 template
- `render_template_string(source, **context)`: Render template from string

## WSGI Compliance

The framework is fully WSGI-compatible and can be deployed with any WSGI server:

```python
from flaskframework import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, WSGI!'

# Use with gunicorn: gunicorn app:app
# Use with uWSGI: uwsgi --http :8000 --wsgi-file app.py --callable app
```

## Development Server

The framework includes a built-in development server based on Python's `wsgiref`:

```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

## Testing

Create test files and run with pytest:

```python
import pytest
from flaskframework import Flask

def test_basic_route():
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello, Test!'
    
    # Test the WSGI application
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'wsgi.input': None
    }
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    assert responses[0][0] == '200 OK'
    assert b'Hello, Test!' in b''.join(result)
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Requirements

- Python 3.11+
- Jinja2 (for template rendering)

The framework has minimal dependencies and is designed to be lightweight while providing essential web development features.
