#!/usr/bin/env python3
"""
Example application demonstrating the Flask framework features.
"""

from flaskframework import Flask, Blueprint, render_template_string, current_app, g

# Create the main application
app = Flask(__name__)
app.debug = True

# Create a blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    """List all users."""
    users = ['alice', 'bob', 'charlie']
    return {'users': users, 'count': len(users)}

@api.route('/users/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID."""
    return {'user_id': user_id, 'name': f'User {user_id}', 'status': 'active'}

@api.route('/users/<name>')
def get_user_by_name(name):
    """Get a user by name."""
    return {'name': name, 'user_id': hash(name) % 1000, 'status': 'active'}

# Register the API blueprint
app.register_blueprint(api)

# Before request handler
@app.before_request
def before_request():
    """Set up request context."""
    g.request_count = getattr(g, 'request_count', 0) + 1
    g.user = {'name': 'Anonymous', 'role': 'guest'}

# Main application routes
@app.route('/')
def index():
    """Home page."""
    template = '''
    <html>
        <head><title>Flask Framework Demo</title></head>
        <body>
            <h1>Welcome to Flask Framework!</h1>
            <p>This is request #{{ g.request_count }}</p>
            <p>Current user: {{ g.user.name }} ({{ g.user.role }})</p>
            <p>Application: {{ current_app.import_name }}</p>
            
            <h2>Available Routes:</h2>
            <ul>
                <li><a href="/">/</a> - This page</li>
                <li><a href="/hello/world">/hello/world</a> - Greeting with name</li>
                <li><a href="/user/123">/user/123</a> - User by ID</li>
                <li><a href="/user/alice">/user/alice</a> - User by name</li>
                <li><a href="/api/users">/api/users</a> - API: List users</li>
                <li><a href="/api/users/42">/api/users/42</a> - API: Get user by ID</li>
                <li><a href="/api/users/bob">/api/users/bob</a> - API: Get user by name</li>
            </ul>
        </body>
    </html>
    '''
    return render_template_string(template)

@app.route('/hello/<name>')
def hello(name):
    """Personalized greeting."""
    template = '''
    <html>
        <head><title>Hello {{ name }}!</title></head>
        <body>
            <h1>Hello, {{ name }}!</h1>
            <p>Welcome to the Flask Framework demo.</p>
            <p>This is request #{{ g.request_count }}</p>
            <p><a href="/">← Back to home</a></p>
        </body>
    </html>
    '''
    return render_template_string(template, name=name)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """User profile page by ID."""
    template = '''
    <html>
        <head><title>User {{ user_id }}</title></head>
        <body>
            <h1>User Profile</h1>
            <p><strong>User ID:</strong> {{ user_id }}</p>
            <p><strong>Name:</strong> User {{ user_id }}</p>
            <p><strong>Type:</strong> Integer ID</p>
            <p>This is request #{{ g.request_count }}</p>
            <p><a href="/">← Back to home</a></p>
        </body>
    </html>
    '''
    return render_template_string(template, user_id=user_id)

@app.route('/user/<name>')
def user_profile_by_name(name):
    """User profile page by name."""
    template = '''
    <html>
        <head><title>User {{ name }}</title></head>
        <body>
            <h1>User Profile</h1>
            <p><strong>Name:</strong> {{ name }}</p>
            <p><strong>User ID:</strong> {{ name|hash % 1000 }}</p>
            <p><strong>Type:</strong> String name</p>
            <p>This is request #{{ g.request_count }}</p>
            <p><a href="/">← Back to home</a></p>
        </body>
    </html>
    '''
    return render_template_string(template, name=name)

@app.route('/data', methods=['POST'])
def handle_data():
    """Handle POST data."""
    return {'message': 'Data received', 'method': 'POST', 'status': 'success'}

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Custom 404 page."""
    template = '''
    <html>
        <head><title>Page Not Found</title></head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The page you requested could not be found.</p>
            <p><a href="/">← Back to home</a></p>
        </body>
    </html>
    '''
    return render_template_string(template), 404

if __name__ == '__main__':
    print("Starting Flask Framework Demo Application...")
    print("Visit http://127.0.0.1:5000/ to see the demo")
    app.run(host='127.0.0.1', port=5000, debug=True)
