# Flask Framework

A WSGI-compatible micro web framework built in Python 3.11 that provides essential web development features including URL routing, request/response handling, template rendering, and modular application structure through blueprints.

## Features

1. **URL Routing with Variable Segments and HTTP Method Filtering**
   - Support for dynamic URL segments like `/user/<int:id>` and `/path/<path:filename>`
   - HTTP method filtering (GET, POST, PUT, DELETE, etc.)
   - Flexible route patterns with type converters

2. **Request Object**
   - Encapsulates HTTP method, path, headers, query string, and body
   - Easy access to form data, JSON, and file uploads
   - Thread-safe request handling

3. **Response Object**
   - Configurable status codes, headers, and body content
   - Support for different content types and encoding
   - WSGI-compatible response format

4. **Jinja2 Template Rendering**
   - Integrated template engine with application context
   - Access to `current_app` and `g` objects in templates
   - Template inheritance and includes support

5. **Application Context Management**
   - Thread-local storage for `current_app` and `g` objects
   - Safe concurrent request handling
   - Context-aware template rendering

6. **Blueprint-based Modular Applications**
   - Organize routes and functionality into reusable modules
   - URL prefix inheritance for blueprint routes
   - Deferred registration pattern

## Installation

```bash
pip install -e .
```

## Quick Start

### Basic Application

```python
from flaskframework import Flask, render_template_string

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

@app.route('/api/data', methods=['POST'])
def api_data():
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(debug=True)
```

### Using Templates

```python
from flaskframework import Flask, render_template_string

app = Flask(__name__)

@app.route('/hello/<name>')
def hello_template(name):
    template = '''
    <html>
        <body>
            <h1>Hello, {{ name }}!</h1>
            <p>Welcome to {{ current_app.import_name }}</p>
        </body>
    </html>
    '''
    return render_template_string(template, name=name)

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

@api.route('/users/<int:user_id>')
def get_user(user_id):
    return {'user_id': user_id, 'name': f'User {user_id}'}

# Create the main application
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
def load_user():
    g.user = {'name': 'Anonymous'}

@app.route('/profile')
def profile():
    return f"Current user: {g.user['name']}"

@app.route('/app-info')
def app_info():
    return f"Application: {current_app.import_name}"

if __name__ == '__main__':
    app.run()
```

## API Reference

### Flask Class

The main application class that handles WSGI requests and routing.

#### Methods

- `route(rule, **options)`: Decorator for adding routes
- `add_url_rule(rule, endpoint, view_func, methods=None)`: Add URL rule programmatically
- `register_blueprint(blueprint, **options)`: Register a blueprint
- `before_request(f)`: Register before-request handler
- `after_request(f)`: Register after-request handler
- `errorhandler(code)`: Register error handler
- `run(host='127.0.0.1', port=5000, debug=None)`: Run development server

### Blueprint Class

Modular application component for organizing related functionality.

#### Methods

- `route(rule, **options)`: Add route to blueprint
- `add_url_rule(rule, endpoint, view_func, methods=None)`: Add URL rule to blueprint

### Request Object

Encapsulates HTTP request data.

#### Properties

- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `args`: Query string arguments
- `headers`: HTTP headers
- `body`: Raw request body as bytes
- `data`: Request body as string
- `content_type`: Content-Type header
- `content_length`: Content-Length header

#### Methods

- `get_json()`: Parse JSON from request body

### Response Object

Represents HTTP response.

#### Properties

- `status_code`: HTTP status code
- `headers`: Response headers
- `data`: Response body as bytes

### Context Objects

- `current_app`: Proxy to current Flask application
- `g`: Application context namespace for storing data

### Template Functions

- `render_template(template_name, **context)`: Render template from file
- `render_template_string(source, **context)`: Render template from string

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

Deploy with gunicorn:
```bash
gunicorn app:application
```

## Development Server

The framework includes a built-in development server based on Python's `wsgiref`:

```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

## Requirements

- Python 3.11+
- Jinja2 3.0.0+ (for template rendering)

## License

MIT License
