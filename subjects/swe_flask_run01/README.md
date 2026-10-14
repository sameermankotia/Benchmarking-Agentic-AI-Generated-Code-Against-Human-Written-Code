# Flask Framework

A WSGI-compatible micro web framework built in Python 3.11. This framework provides all the essential features needed for modern web development while maintaining simplicity and flexibility.

## Features

1. **URL Routing with Variable Segments and HTTP Method Filtering**
   - Support for dynamic URL patterns like `/user/<int:id>`
   - HTTP method filtering (GET, POST, PUT, DELETE, etc.)
   - Flexible route matching with type converters

2. **Request Object**
   - Encapsulates HTTP method, path, headers, query string, and body
   - Easy access to form data and JSON payloads
   - Comprehensive request information parsing

3. **Response Object**
   - Configurable status codes, headers, and body content
   - Support for various response types (HTML, JSON, etc.)
   - Cookie management

4. **Jinja2 Template Rendering**
   - Integrated template engine with application context
   - Template inheritance and includes
   - Automatic HTML escaping for security

5. **Application Context Management**
   - Thread-local storage for `current_app` and `g` objects
   - Safe concurrent request handling
   - Context-aware template rendering

6. **Blueprint-based Modular Applications**
   - Organize routes into reusable blueprints
   - URL prefix inheritance
   - Modular application architecture

## Installation

```bash
pip install -e .
```

## Quick Start

### Basic Application

```python
from flaskframework import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/user/<name>')
def user(name):
    return f'Hello, {name}!'

@app.route('/api/data', methods=['POST'])
def api_data():
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(debug=True)
```

### Using Blueprints

```python
from flaskframework import Flask, Blueprint

# Create a blueprint
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    return {'users': ['alice', 'bob']}

@api.route('/users/<int:user_id>')
def get_user(user_id):
    return {'user_id': user_id}

# Create the main app
app = Flask(__name__)
app.register_blueprint(api)

@app.route('/')
def index():
    return 'Welcome to the API!'

if __name__ == '__main__':
    app.run()
```

### Template Rendering

```python
from flaskframework import Flask, render_template

app = Flask(__name__)

@app.route('/hello/<name>')
def hello(name):
    return render_template('hello.html', name=name)

if __name__ == '__main__':
    app.run()
```

Create `templates/hello.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Hello</title>
</head>
<body>
    <h1>Hello, {{ name }}!</h1>
</body>
</html>
```

### Application Context

```python
from flaskframework import Flask, current_app, g

app = Flask(__name__)

@app.before_request
def load_user():
    g.user = 'current_user'

@app.route('/profile')
def profile():
    return f'Profile for {g.user}'

@app.route('/app-info')
def app_info():
    return f'App name: {current_app.import_name}'

if __name__ == '__main__':
    app.run()
```

### Error Handling

```python
from flaskframework import Flask

app = Flask(__name__)

@app.errorhandler(404)
def not_found(error):
    return 'Page not found', 404

@app.errorhandler(500)
def internal_error(error):
    return 'Internal server error', 500

@app.route('/error')
def trigger_error():
    raise Exception('This is a test error')

if __name__ == '__main__':
    app.run(debug=True)
```

## API Reference

### Flask Class

The main application class that handles routing, request processing, and WSGI compatibility.

#### Methods

- `route(rule, methods=None)`: Decorator for adding routes
- `add_url_rule(rule, endpoint, view_func, methods)`: Add URL rule programmatically
- `register_blueprint(blueprint, **options)`: Register a blueprint
- `errorhandler(code_or_exception)`: Decorator for error handlers
- `before_request(func)`: Register before-request handler
- `after_request(func)`: Register after-request handler
- `run(host, port, debug, **options)`: Run development server

### Blueprint Class

Organize routes and handlers into reusable modules.

#### Methods

- `route(rule, methods=None)`: Add route to blueprint
- `add_url_rule(rule, endpoint, view_func, methods)`: Add URL rule to blueprint

### Request Object

Access HTTP request data.

#### Properties

- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `headers`: Request headers
- `query_string`: Raw query string
- `args`: Parsed query parameters
- `body`: Request body as bytes
- `data`: Request body as string
- `form`: Parsed form data

### Response Object

Create HTTP responses.

#### Methods

- `set_cookie(key, value, **options)`: Set response cookie

### Context Objects

- `current_app`: Access current application instance
- `g`: Store data during request processing

## WSGI Compliance

The framework is fully WSGI-compatible and can be deployed with any WSGI server:

```python
from flaskframework import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, WSGI!'

# WSGI application callable
application = app
```

Deploy with Gunicorn:
```bash
gunicorn app:application
```

## Development Server

The framework includes a built-in development server for testing:

```python
app.run(host='127.0.0.1', port=5000, debug=True)
```

## Requirements

- Python 3.11+
- Jinja2 (for template rendering)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
