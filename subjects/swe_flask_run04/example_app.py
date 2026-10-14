#!/usr/bin/env python3
"""
Example Flask application demonstrating all framework features.
"""

from flaskframework import Flask, Blueprint, render_template_string, current_app, g

# Create the main application
app = Flask(__name__)

# Create a blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    """List all users."""
    return {'users': ['alice', 'bob', 'charlie']}

@api.route('/users/<int:id>')
def get_user(id):
    """Get a specific user by ID."""
    return {'user_id': id, 'name': f'User {id}'}

@api.route('/users/<name>')
def get_user_by_name(name):
    """Get a user by name."""
    return {'name': name, 'status': 'active'}

# Register the blueprint
app.register_blueprint(api)

# Before request handler
@app.before_request
def before_request():
    g.request_count = getattr(g, 'request_count', 0) + 1

# Main application routes
@app.route('/')
def index():
    """Home page with template rendering."""
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Framework Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #333; }
            .nav { margin: 20px 0; }
            .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
            .nav a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1 class="header">Welcome to Flask Framework!</h1>
        <p>This is a demonstration of the WSGI-compatible micro web framework.</p>
        
        <div class="nav">
            <strong>Try these routes:</strong><br>
            <a href="/">Home</a>
            <a href="/hello/World">Hello World</a>
            <a href="/user/123">User by ID</a>
            <a href="/user/alice">User by Name</a>
            <a href="/api/users">API Users</a>
            <a href="/api/users/42">API User by ID</a>
            <a href="/context">Context Demo</a>
        </div>
        
        <p><strong>Framework Features:</strong></p>
        <ul>
            <li>✓ URL routing with variable segments</li>
            <li>✓ HTTP method filtering</li>
            <li>✓ Request/Response objects</li>
            <li>✓ Jinja2 template rendering</li>
            <li>✓ Application context management</li>
            <li>✓ Blueprint-based modular applications</li>
            <li>✓ WSGI compliance</li>
            <li>✓ Built-in development server</li>
        </ul>
        
        <p><em>Request count: {{ request_count }}</em></p>
    </body>
    </html>
    '''
    return render_template_string(template, request_count=g.request_count)

@app.route('/hello/<name>')
def hello(name):
    """Personalized greeting."""
    template = '''
    <h1>Hello, {{ name }}!</h1>
    <p>This demonstrates URL variable segments.</p>
    <a href="/">← Back to home</a>
    '''
    return render_template_string(template, name=name)

@app.route('/user/<int:id>')
def user_by_id(id):
    """Get user by integer ID."""
    template = '''
    <h2>User Profile</h2>
    <p><strong>User ID:</strong> {{ user_id }}</p>
    <p><strong>Type:</strong> Integer ID</p>
    <a href="/">← Back to home</a>
    '''
    return render_template_string(template, user_id=id)

@app.route('/user/<name>')
def user_by_name(name):
    """Get user by string name."""
    template = '''
    <h2>User Profile</h2>
    <p><strong>Username:</strong> {{ username }}</p>
    <p><strong>Type:</strong> String name</p>
    <a href="/">← Back to home</a>
    '''
    return render_template_string(template, username=name)

@app.route('/context')
def context_demo():
    """Demonstrate application context."""
    template = '''
    <h2>Application Context Demo</h2>
    <p><strong>Current App:</strong> {{ app_name }}</p>
    <p><strong>Request Count:</strong> {{ request_count }}</p>
    <p>This demonstrates thread-local storage with current_app and g objects.</p>
    <a href="/">← Back to home</a>
    '''
    return render_template_string(
        template, 
        app_name=current_app.import_name,
        request_count=g.request_count
    )

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Custom 404 error page."""
    template = '''
    <h1>Page Not Found</h1>
    <p>The requested page could not be found.</p>
    <a href="/">← Back to home</a>
    '''
    return render_template_string(template), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error page."""
    template = '''
    <h1>Internal Server Error</h1>
    <p>Something went wrong on the server.</p>
    <a href="/">← Back to home</a>
    '''
    return render_template_string(template), 500

if __name__ == '__main__':
    print("Starting Flask Framework Demo Application...")
    print("Visit http://127.0.0.1:5000/ to see the demo")
    app.run(host='127.0.0.1', port=5000, debug=True)
