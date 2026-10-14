#!/usr/bin/env python3
"""
Example application demonstrating the Flask Framework features.
"""

from flaskframework import Flask, Blueprint, current_app, g, render_template_string

# Create the main application
app = Flask(__name__)

# Create a blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/users')
def list_users():
    """List all users."""
    users = ['alice', 'bob', 'charlie']
    return {'users': users}

@api.route('/users/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID."""
    return {'user_id': user_id, 'name': f'User {user_id}'}

@api.route('/data', methods=['POST'])
def post_data():
    """Handle POST data."""
    return {'status': 'success', 'message': 'Data received'}

# Register the API blueprint
app.register_blueprint(api)

# Main application routes
@app.route('/')
def index():
    """Home page."""
    template = """
    <html>
    <head><title>Flask Framework Demo</title></head>
    <body>
        <h1>Welcome to Flask Framework!</h1>
        <p>This is a demonstration of the micro web framework.</p>
        <ul>
            <li><a href="/hello/world">Hello World</a></li>
            <li><a href="/user/alice">User Profile</a></li>
            <li><a href="/user/123">User by ID</a></li>
            <li><a href="/api/users">API Users</a></li>
            <li><a href="/api/users/1">API User 1</a></li>
        </ul>
    </body>
    </html>
    """
    return template

@app.route('/hello/<name>')
def hello(name):
    """Personalized greeting."""
    template = """
    <html>
    <head><title>Hello {{ name }}</title></head>
    <body>
        <h1>Hello, {{ name }}!</h1>
        <p>Welcome to the Flask Framework demo.</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """
    return render_template_string(template, name=name)

@app.route('/user/<name>')
def user_profile(name):
    """User profile page."""
    template = """
    <html>
    <head><title>{{ user.name }}'s Profile</title></head>
    <body>
        <h1>{{ user.name }}'s Profile</h1>
        <p>Age: {{ user.age }}</p>
        <p>Email: {{ user.email }}</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """
    user_data = {
        'name': name.title(),
        'age': 25,
        'email': f'{name}@example.com'
    }
    return render_template_string(template, user=user_data)

@app.route('/user/<int:user_id>')
def user_by_id(user_id):
    """User profile by ID."""
    template = """
    <html>
    <head><title>User {{ user_id }}</title></head>
    <body>
        <h1>User Profile #{{ user_id }}</h1>
        <p>This user has ID: {{ user_id }}</p>
        <p>Type: {{ user_type }}</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """
    return render_template_string(template, user_id=user_id, user_type=type(user_id).__name__)

@app.before_request
def before_request():
    """Set up request context."""
    g.request_count = getattr(g, 'request_count', 0) + 1

@app.route('/context')
def show_context():
    """Demonstrate application context."""
    template = """
    <html>
    <head><title>Context Demo</title></head>
    <body>
        <h1>Application Context Demo</h1>
        <p>App name: {{ app_name }}</p>
        <p>Request count: {{ request_count }}</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """
    return render_template_string(template, 
                                app_name=current_app.import_name,
                                request_count=g.request_count)

@app.errorhandler(404)
def not_found(error):
    """Custom 404 page."""
    template = """
    <html>
    <head><title>Page Not Found</title></head>
    <body>
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """
    return render_template_string(template), 404

if __name__ == '__main__':
    print("Starting Flask Framework Demo Application...")
    print("Visit http://127.0.0.1:5000 to see the demo")
    app.run(host='127.0.0.1', port=5000, debug=True)
