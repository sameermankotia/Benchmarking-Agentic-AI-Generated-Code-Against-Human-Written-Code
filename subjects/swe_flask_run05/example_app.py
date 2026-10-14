#!/usr/bin/env python3
"""
Example application demonstrating FlaskFramework features.
"""

from flaskframework import Flask, Blueprint, render_template, current_app, g

# Create the main application
app = Flask(__name__)

# Create a blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    """List all users."""
    return {'users': ['alice', 'bob', 'charlie']}

@api.route('/users/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID."""
    return {'user_id': user_id, 'name': f'User {user_id}'}

@api.route('/users', methods=['POST'])
def create_user():
    """Create a new user."""
    return {'message': 'User created', 'id': 123}, 201

# Register the API blueprint
app.register_blueprint(api)

# Main application routes
@app.route('/')
def index():
    """Home page."""
    return '''
    <h1>Welcome to FlaskFramework!</h1>
    <p>A WSGI-compatible micro web framework</p>
    <ul>
        <li><a href="/hello/World">Say hello</a></li>
        <li><a href="/user/42">User profile</a></li>
        <li><a href="/api/users">API: List users</a></li>
        <li><a href="/api/users/1">API: Get user 1</a></li>
    </ul>
    '''

@app.route('/hello/<name>')
def hello(name):
    """Personalized greeting."""
    return f'<h1>Hello, {name}!</h1><p><a href="/">Back to home</a></p>'

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """User profile page."""
    return f'''
    <h1>User Profile</h1>
    <p>User ID: {user_id}</p>
    <p>This demonstrates integer URL parameters.</p>
    <p><a href="/">Back to home</a></p>
    '''

@app.route('/context-demo')
def context_demo():
    """Demonstrate application context."""
    g.demo_value = "Hello from g!"
    app_name = current_app.import_name
    return f'''
    <h1>Context Demo</h1>
    <p>Application name: {app_name}</p>
    <p>Value from g: {g.demo_value}</p>
    <p><a href="/">Back to home</a></p>
    '''

# Error handlers
@app.errorhandler(404)
def not_found():
    """Custom 404 page."""
    return '''
    <h1>Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <p><a href="/">Go home</a></p>
    ''', 404

@app.errorhandler(500)
def server_error(error):
    """Custom 500 page."""
    return '''
    <h1>Internal Server Error</h1>
    <p>Something went wrong on our end.</p>
    <p><a href="/">Go home</a></p>
    ''', 500

if __name__ == '__main__':
    print("Starting FlaskFramework example application...")
    print("Visit http://127.0.0.1:5000/ to see the demo")
    app.run(debug=True)
