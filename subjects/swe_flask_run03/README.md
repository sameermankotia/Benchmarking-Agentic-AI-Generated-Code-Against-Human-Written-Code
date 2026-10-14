# Flask Framework

A WSGI-compatible micro web framework built in Python 3.11 that provides essential web development features including URL routing, request/response handling, template rendering, application context management, and modular blueprints.

## Features

1. **URL Routing with Variable Segments and HTTP Method Filtering**
   - Support for dynamic URL segments like `/user/<int:id>`
   - HTTP method filtering (GET, POST, PUT, DELETE, etc.)
   - Flexible route patterns with type converters

2. **Request Object**
   - Encapsulates HTTP method, path, headers, query string, and body
   - Easy access to request data and parameters
   - JSON parsing support

3. **Response Object**
   - Configurable status codes, headers, and body content
   - WSGI-compatible response formatting
   - Support for different content types

4. **Jinja2 Template Rendering**
   - Integrated template engine with application context
   - Automatic template loading from templates directory
   - Fallback to simple string replacement if Jinja2 unavailable

5. **Application Context Management**
   - Thread-local storage for `current_app` and `g` objects
   - Safe concurrent request handling
   - Context-aware template rendering

6. **Blueprint-based Modular Applications**
   - Organize routes into reusable blueprints
   - URL prefix inheritance and customization
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

@app.route('/user/<int:user_id>')
def user_by_id(user_id):
    return f'User ID: {user_id}'

if __name__ == '__main__':
    app.run(debug=True)
```

### Using Templates

Create a `templates/index.html` file:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>Welcome, {{ name }}!</p>
</body>
</html>
```

```python
from flaskframework import Flask, render_template

app = Flask(__name__)

@app.route('/welcome/<name>')
def welcome(name):
    return render_template('index.html', 
                         title='Welcome Page',
                         heading='Welcome!',
                         name=name)

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
    return 'List of users'

@api.route('/users/<int:user_id>')
def get_user(user_id):
    return f'User {user_id}'

# Create main app and register blueprint
app = Flask(__name__)
app.register_blueprint(api)

@app.route('/')
def index():
    return 'Main page'

if __name__ == '__main__':
    app.run()
```

### Application Context

```python
from flaskframework import Flask, current_app, g

app = Flask(__name__)

@app.route('/info')
def app_info():
    # Access current app
    app_name = current_app.import_name
    
    # Store data in g for request duration
    g.request_count = getattr(g, 'request_count', 0) + 1
    
    return f'App: {app_name}, Request count: {g.request_count}'

if __name__ == '__main__':
    app.run()
```

### HTTP Methods and Error Handling

```python
from flaskframework import Flask, Response

app = Flask(__name__)

@app.route('/data', methods=['GET', 'POST'])
def handle_data():
    from flaskframework.context import current_app
    # Access request through WSGI environ (simplified example)
    return 'Data endpoint'

@app.errorhandler(404)
def not_found(error):
    return Response('Page not found', status=404)

@app.errorhandler(500)
def internal_error(error):
    return Response('Internal server error', status=500)

if __name__ == '__main__':
    app.run()
```

## API Reference

### Flask Class

- `Flask(import_name, template_folder='templates')` - Create a new Flask application
- `route(rule, methods=None)` - Decorator to register a route
- `add_url_rule(rule, endpoint, view_func, methods=None)` - Add a URL rule
- `register_blueprint(blueprint, **options)` - Register a blueprint
- `errorhandler(code_or_exception)` - Register an error handler
- `run(host='127.0.0.1', port=5000, debug=False)` - Run development server

### Blueprint Class

- `Blueprint(name, import_name, url_prefix=None)` - Create a new blueprint
- `route(rule, methods=None)` - Decorator to register a route with the blueprint
- `add_url_rule(rule, endpoint, view_func, methods=None)` - Add a URL rule to the blueprint

### Request Object

- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path
- `headers` - Request headers dictionary
- `query_string` - Raw query string
- `args` - Parsed query parameters
- `body` - Request body as bytes
- `json` - Parsed JSON data (if Content-Type is application/json)

### Response Object

- `Response(body='', status=200, headers=None, content_type='text/html')` - Create a response
- `status_code` - HTTP status code
- `headers` - Response headers dictionary
- `body` - Response body

### Context Objects

- `current_app` - Proxy to the current Flask application
- `g` - Application context global object for storing data during a request

### Template Functions

- `render_template(template_name, **context)` - Render a Jinja2 template

## WSGI Compliance

This framework is fully WSGI-compatible and can be deployed with any WSGI server:

```python
# For production deployment
from flaskframework import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Production!'

# WSGI application callable
application = app
```

Deploy with Gunicorn:
```bash
gunicorn app:application
```

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Project Structure

```
flaskframework/
├── __init__.py          # Main package exports
├── app.py              # Flask application class
├── blueprints.py       # Blueprint implementation
├── context.py          # Application context and thread-local storage
├── request.py          # Request object implementation
├── response.py         # Response object implementation
├── routing.py          # URL routing and pattern matching
└── templating.py       # Template rendering with Jinja2
```

## Requirements

- Python 3.11+
- Jinja2 (optional, for template rendering)

## License

MIT License
