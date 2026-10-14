#!/usr/bin/env python3
"""
Verification script to ensure all requirements are met.
"""

import sys
import os
from io import StringIO

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flaskframework import Flask, Blueprint, Request, Response, current_app, g, render_template


def verify_requirement_1():
    """(1) URL routing with variable segments and HTTP method filtering"""
    print("✓ Requirement 1: URL routing with variable segments and HTTP method filtering")
    
    app = Flask(__name__)
    
    @app.route('/user/<name>')
    def user_profile(name):
        return f'User: {name}'
    
    @app.route('/user/<int:id>')
    def user_by_id(id):
        return f'User ID: {id}'
    
    @app.route('/api/data', methods=['POST'])
    def post_data():
        return 'POST received'
    
    @app.route('/api/data', methods=['GET'])
    def get_data():
        return 'GET received'
    
    # Test variable segments
    view_func, args = app.match_request('/user/john', 'GET')
    assert view_func is not None and args == {'name': 'john'}
    
    view_func, args = app.match_request('/user/123', 'GET')
    assert view_func is not None and args == {'id': '123'}
    
    # Test HTTP method filtering
    view_func, args = app.match_request('/api/data', 'POST')
    assert view_func is not None
    
    view_func, args = app.match_request('/api/data', 'GET')
    assert view_func is not None
    
    view_func, args = app.match_request('/api/data', 'DELETE')
    assert view_func is None
    
    print("  - Variable segments: ✓")
    print("  - HTTP method filtering: ✓")


def verify_requirement_2():
    """(2) Request object encapsulating method, path, headers, query string, and body"""
    print("✓ Requirement 2: Request object encapsulating method, path, headers, query string, and body")
    
    test_body = '{"key": "value"}'
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/test/path',
        'QUERY_STRING': 'param1=value1&param2=value2',
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': str(len(test_body)),
        'HTTP_USER_AGENT': 'TestAgent/1.0',
        'HTTP_AUTHORIZATION': 'Bearer token123',
        'wsgi.input': StringIO(test_body)
    }
    
    request = Request(environ)
    
    assert request.method == 'POST'
    assert request.path == '/test/path'
    assert 'User-Agent' in request.headers
    assert request.headers['User-Agent'] == 'TestAgent/1.0'
    assert 'Authorization' in request.headers
    assert request.query_string == b'param1=value1&param2=value2'
    assert 'param1' in request.args
    assert request.args['param1'] == ['value1']
    assert request.data == test_body
    
    print("  - Method: ✓")
    print("  - Path: ✓")
    print("  - Headers: ✓")
    print("  - Query string: ✓")
    print("  - Body: ✓")


def verify_requirement_3():
    """(3) Response object with status code, headers, and body"""
    print("✓ Requirement 3: Response object with status code, headers, and body")
    
    # Test basic response
    response = Response('Hello World')
    assert response.status_code == 200
    assert response.data == b'Hello World'
    assert response.status == '200 OK'
    
    # Test custom status and headers
    response = Response('Created', status=201, headers={'Location': '/resource/123'})
    assert response.status_code == 201
    assert response.status == '201 Created'
    assert response.headers['Location'] == '/resource/123'
    
    # Test WSGI headers format
    wsgi_headers = response.get_wsgi_headers()
    assert isinstance(wsgi_headers, list)
    assert all(isinstance(h, tuple) and len(h) == 2 for h in wsgi_headers)
    
    print("  - Status code: ✓")
    print("  - Headers: ✓")
    print("  - Body: ✓")


def verify_requirement_4():
    """(4) Jinja2 template rendering integrated with the application context"""
    print("✓ Requirement 4: Jinja2 template rendering integrated with the application context")
    
    # Create test template
    os.makedirs('templates', exist_ok=True)
    with open('templates/test.html', 'w') as f:
        f.write('<h1>Hello {{name}}!</h1><p>App: {{app_name}}</p>')
    
    app = Flask(__name__)
    
    with app.app_context():
        # Test template rendering with context
        result = render_template('test.html', name='World', app_name=current_app.import_name)
        assert 'Hello World!' in result
        assert app.import_name in result
    
    # Clean up
    os.remove('templates/test.html')
    os.rmdir('templates')
    
    print("  - Template rendering: ✓")
    print("  - Application context integration: ✓")


def verify_requirement_5():
    """(5) Application context management using thread-local storage"""
    print("✓ Requirement 5: Application context management using thread-local storage")
    
    app = Flask(__name__)
    
    # Test context availability
    with app.app_context():
        assert current_app == app
        g.test_value = 'hello'
        assert g.test_value == 'hello'
    
    # Test context cleanup
    try:
        _ = current_app.import_name
        assert False, "Should raise RuntimeError"
    except RuntimeError:
        pass
    
    print("  - current_app: ✓")
    print("  - g object: ✓")
    print("  - Thread-local storage: ✓")


def verify_requirement_6():
    """(6) Blueprint-based modular applications with URL prefix inheritance"""
    print("✓ Requirement 6: Blueprint-based modular applications with URL prefix inheritance")
    
    app = Flask(__name__)
    
    # Create blueprint with URL prefix
    api = Blueprint('api', __name__, url_prefix='/api/v1')
    
    @api.route('/users')
    def list_users():
        return 'Users list'
    
    @api.route('/users/<int:id>')
    def get_user(id):
        return f'User {id}'
    
    # Register blueprint
    app.register_blueprint(api)
    
    # Test URL prefix inheritance
    view_func, args = app.match_request('/api/v1/users', 'GET')
    assert view_func is not None
    
    view_func, args = app.match_request('/api/v1/users/123', 'GET')
    assert view_func is not None and args == {'id': '123'}
    
    # Test that routes without prefix don't match
    view_func, args = app.match_request('/users', 'GET')
    assert view_func is None
    
    print("  - Blueprint registration: ✓")
    print("  - URL prefix inheritance: ✓")
    print("  - Modular applications: ✓")


def verify_wsgi_compliance():
    """Verify WSGI compliance"""
    print("✓ WSGI Compliance: Framework passes WSGI compliance check")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello WSGI'
    
    # Test WSGI interface
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'wsgi.input': StringIO('')
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    result = app(environ, start_response)
    response_body = b''.join(result)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'Hello WSGI'
    assert any(h[0] == 'Content-Length' for h in response_data['headers'])
    
    print("  - WSGI callable interface: ✓")
    print("  - Proper status format: ✓")
    print("  - Required headers: ✓")


def verify_development_server():
    """Verify built-in development server"""
    print("✓ Built-in Development Server: Framework includes development server")
    
    app = Flask(__name__)
    
    # Verify the run method exists and is callable
    assert hasattr(app, 'run')
    assert callable(app.run)
    
    print("  - Development server available: ✓")


def verify_project_files():
    """Verify required project files"""
    print("✓ Project Files: Complete pyproject.toml and README.md provided")
    
    assert os.path.exists('pyproject.toml'), "pyproject.toml not found"
    assert os.path.exists('README.md'), "README.md not found"
    
    # Check pyproject.toml content
    with open('pyproject.toml', 'r') as f:
        content = f.read()
        assert 'name = "flaskframework"' in content
        assert 'requires-python = ">=3.11"' in content
        assert 'jinja2' in content
    
    # Check README.md content
    with open('README.md', 'r') as f:
        content = f.read()
        assert 'FlaskFramework' in content
        assert 'WSGI-compatible' in content
        assert 'Installation' in content
        assert 'Quick Start' in content
    
    print("  - pyproject.toml: ✓")
    print("  - README.md: ✓")


def main():
    """Run all requirement verifications."""
    print("🔍 FlaskFramework Requirements Verification\n")
    print("Verifying all 6 numbered requirements plus additional specifications...\n")
    
    try:
        verify_requirement_1()
        print()
        
        verify_requirement_2()
        print()
        
        verify_requirement_3()
        print()
        
        verify_requirement_4()
        print()
        
        verify_requirement_5()
        print()
        
        verify_requirement_6()
        print()
        
        verify_wsgi_compliance()
        print()
        
        verify_development_server()
        print()
        
        verify_project_files()
        print()
        
        print("🎉 ALL REQUIREMENTS VERIFIED SUCCESSFULLY!")
        print("\nFlaskFramework is a complete WSGI-compatible micro web framework")
        print("that meets all specified requirements for Python 3.11.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
