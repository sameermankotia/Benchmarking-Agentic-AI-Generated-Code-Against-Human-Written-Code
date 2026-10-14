#!/usr/bin/env python3
"""
WSGI deployment file for FlaskFramework application.
Use with any WSGI server like Gunicorn, uWSGI, or mod_wsgi.

Example usage:
    gunicorn wsgi:application
    uwsgi --http :8000 --wsgi-file wsgi.py --callable application
"""

from flaskframework import Flask, Blueprint

# Create the application
app = Flask(__name__)

# Create API blueprint
api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'FlaskFramework'}

@api.route('/info')
def app_info():
    """Application information."""
    return {
        'name': 'FlaskFramework Demo',
        'version': '1.0.0',
        'framework': 'FlaskFramework'
    }

# Register blueprint
app.register_blueprint(api)

# Main routes
@app.route('/')
def index():
    """Main index page."""
    return '''
    <h1>FlaskFramework Production Deployment</h1>
    <p>This application is running on a WSGI server.</p>
    <ul>
        <li><a href="/api/v1/health">Health Check</a></li>
        <li><a href="/api/v1/info">App Info</a></li>
    </ul>
    '''

@app.route('/hello/<name>')
def hello(name):
    """Personalized greeting."""
    return f'<h1>Hello, {name}!</h1>'

# Error handlers
@app.errorhandler(404)
def not_found():
    return {'error': 'Not Found', 'code': 404}, 404

@app.errorhandler(500)
def server_error(error):
    return {'error': 'Internal Server Error', 'code': 500}, 500

# WSGI application object
application = app

if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=8000, debug=False)
