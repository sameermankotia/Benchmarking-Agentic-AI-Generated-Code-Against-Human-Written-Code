# FlaskFramework

A WSGI-compatible micro web framework in Python 3.11 with Flask-like features.

## Features

FlaskFramework provides all the essential features needed for modern web development:

1. **URL Routing with Variable Segments and HTTP Method Filtering**
   - Support for dynamic URL segments like `/user/<int:id>` and `/path/<path:filename>`
   - HTTP method filtering (GET, POST, PUT, DELETE, etc.)
   - Regex-based URL matching for flexibility

2. **Request Object**
   - Encapsulates HTTP method, path, headers, query string, and body
   - Easy access to form data and JSON payloads
   - Thread-safe request handling

3. **Response Object**
   - Configurable status codes, headers, and body content
   - WSGI-compatible response format
   - Support for different content types

4. **Jinja2 Template Rendering**
   - Integrated template engine with application context
   - Fallback to simple string substitution if Jinja2 not available
   - Template folder configuration

5. **Application Context Management**
   - Thread-local storage for `current_app` and `g` objects
   - Context managers for proper cleanup
   - Flask-compatible context handling

6. **Blueprint-based Modular Applications**
   - URL prefix inheritance for organized routing
   - Modular application structure
   - Easy blueprint registration

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

@app.route('/api/data', methods=['POST'])
def api_data():
    # Access request data
    from flaskframework import current_app, g
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(debug=True)
```

### Using Blueprints

```python
from flaskframework import Flask, Blueprint

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    return {'users': []}

@api.route('/users/<int:id>')
def get_user(id):
    return {'user_id': id}

# Create app and register blueprint
app = Flask(__name__)
app.register_blueprint(api)

if __name__ == '__main__':
    app.run()
```

### Template Rendering

```python
from flaskframework import Flask, render_template

app = Flask(__name__, template_folder='templates')

@app.route('/hello/<name>')
def hello_template(name):
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
    <h1>Hello, {{name}}!</h1>
</body>
</html>
```

### Error Handling

```python
from flaskframework import Flask

app = Flask(__name__)

@app.errorhandler(404)
def not_found():
    return 'Page not found', 404

@app.errorhandler(500)
def server_error(error):
    return 'Internal server error', 500

if __name__ == '__main__':
    app.run()
```

## WSGI Compatibility

FlaskFramework is fully WSGI-compatible and can be deployed with any WSGI server:

```python
# wsgi.py
from flaskframework import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from WSGI!'

# WSGI application
application = app
```

Deploy with Gunicorn:
```bash
gunicorn wsgi:application
```

## Development Server

FlaskFramework includes a built-in development server based on Python's `wsgiref`:

```python
app.run(host='127.0.0.1', port=5000, debug=True)
```

## API Reference

### Flask Class

- `Flask(import_name, template_folder='templates')` - Create application instance
- `route(rule, methods=['GET'])` - Decorator for URL routing
- `register_blueprint(blueprint, **options)` - Register a blueprint
- `errorhandler(code)` - Decorator for error handlers
- `run(host='127.0.0.1', port=5000, debug=False)` - Run development server

### Blueprint Class

- `Blueprint(name, import_name, url_prefix=None)` - Create blueprint
- `route(rule, methods=['GET'])` - Register route with blueprint

### Request Object

- `method` - HTTP method
- `path` - Request path
- `headers` - Request headers
- `query_string` - Raw query string
- `args` - Parsed query parameters
- `body` - Request body as bytes
- `data` - Request body as string
- `get_json()` - Parse JSON body

### Response Object

- `Response(response, status=200, headers=None, mimetype='text/html')`
- `status_code` - HTTP status code
- `headers` - Response headers
- `data` - Response body

### Context Objects

- `current_app` - Current application instance (thread-local)
- `g` - Application context globals (thread-local)

## Requirements

- Python 3.11+
- Jinja2 (optional, for template rendering)

## License

MIT License
