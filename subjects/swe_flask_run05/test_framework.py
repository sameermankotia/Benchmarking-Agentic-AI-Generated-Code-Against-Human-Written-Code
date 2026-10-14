#!/usr/bin/env python3
"""
Comprehensive test script for FlaskFramework.
Tests all required features: routing, request/response, templates, context, blueprints.
"""

import sys
import os
import threading
import time
from io import StringIO

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flaskframework import Flask, Blueprint, Request, Response, current_app, g, render_template


def test_basic_routing():
    """Test basic URL routing functionality."""
    print("Testing basic routing...")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello World'
    
    @app.route('/test')
    def test():
        return 'Test Page'
    
    # Test route matching
    view_func, args = app.match_request('/', 'GET')
    assert view_func is not None, "Should match root route"
    assert args == {}, "No URL args expected"
    
    view_func, args = app.match_request('/test', 'GET')
    assert view_func is not None, "Should match test route"
    
    view_func, args = app.match_request('/nonexistent', 'GET')
    assert view_func is None, "Should not match nonexistent route"
    
    print("✓ Basic routing works")


def test_variable_segments():
    """Test URL routing with variable segments."""
    print("Testing variable segments...")
    
    app = Flask(__name__)
    
    @app.route('/user/<name>')
    def user_profile(name):
        return f'User: {name}'
    
    @app.route('/user/<int:id>')
    def user_by_id(id):
        return f'User ID: {id}'
    
    @app.route('/file/<path:filename>')
    def serve_file(filename):
        return f'File: {filename}'
    
    # Test string variable
    view_func, args = app.match_request('/user/john', 'GET')
    assert view_func is not None, "Should match user profile route"
    assert args == {'name': 'john'}, f"Expected name=john, got {args}"
    
    # Test int variable
    view_func, args = app.match_request('/user/123', 'GET')
    assert view_func is not None, "Should match user ID route"
    assert args == {'id': '123'}, f"Expected id=123, got {args}"
    
    # Test path variable
    view_func, args = app.match_request('/file/docs/readme.txt', 'GET')
    assert view_func is not None, "Should match file route"
    assert args == {'filename': 'docs/readme.txt'}, f"Expected filename=docs/readme.txt, got {args}"
    
    print("✓ Variable segments work")


def test_http_methods():
    """Test HTTP method filtering."""
    print("Testing HTTP method filtering...")
    
    app = Flask(__name__)
    
    @app.route('/api/data', methods=['POST'])
    def post_data():
        return 'POST received'
    
    @app.route('/api/data', methods=['GET'])
    def get_data():
        return 'GET received'
    
    # Test POST method
    view_func, args = app.match_request('/api/data', 'POST')
    assert view_func is not None, "Should match POST route"
    
    # Test GET method
    view_func, args = app.match_request('/api/data', 'GET')
    assert view_func is not None, "Should match GET route"
    
    # Test unsupported method
    view_func, args = app.match_request('/api/data', 'DELETE')
    assert view_func is None, "Should not match DELETE method"
    
    print("✓ HTTP method filtering works")


def test_request_object():
    """Test Request object functionality."""
    print("Testing Request object...")
    
    # Mock WSGI environ
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/test',
        'QUERY_STRING': 'param1=value1&param2=value2',
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': '13',
        'HTTP_USER_AGENT': 'TestAgent/1.0',
        'wsgi.input': StringIO('{"test": true}')
    }
    
    request = Request(environ)
    
    assert request.method == 'POST', f"Expected POST, got {request.method}"
    assert request.path == '/test', f"Expected /test, got {request.path}"
    assert 'User-Agent' in request.headers, "Should have User-Agent header"
    assert request.headers['User-Agent'] == 'TestAgent/1.0', "User-Agent should match"
    assert 'param1' in request.args, "Should parse query parameters"
    assert request.args['param1'] == ['value1'], "Should parse param1 correctly"
    
    print("✓ Request object works")


def test_response_object():
    """Test Response object functionality."""
    print("Testing Response object...")
    
    # Test basic response
    response = Response('Hello World')
    assert response.status_code == 200, "Default status should be 200"
    assert response.data == b'Hello World', "Data should be encoded"
    
    # Test custom status and headers
    response = Response('Not Found', status=404, headers={'Custom': 'Header'})
    assert response.status_code == 404, "Status should be 404"
    assert response.headers['Custom'] == 'Header', "Custom header should be set"
    assert response.status == '404 Not Found', "Status line should be formatted"
    
    # Test WSGI headers
    wsgi_headers = response.get_wsgi_headers()
    header_dict = dict(wsgi_headers)
    assert 'Content-Length' in header_dict, "Should include Content-Length"
    assert 'Custom' in header_dict, "Should include custom headers"
    
    print("✓ Response object works")


def test_application_context():
    """Test application context management."""
    print("Testing application context...")
    
    app = Flask(__name__)
    
    # Test context manager
    with app.app_context():
        assert current_app == app, "current_app should be available in context"
        g.test_value = 'test'
        assert g.test_value == 'test', "g should store values"
    
    # Test that context is cleaned up
    try:
        _ = current_app.import_name  # Try to access an attribute
        assert False, "current_app should not be available outside context"
    except RuntimeError:
        pass  # Expected
    
    print("✓ Application context works")


def test_blueprints():
    """Test Blueprint functionality."""
    print("Testing Blueprints...")
    
    app = Flask(__name__)
    
    # Create blueprint
    api = Blueprint('api', __name__, url_prefix='/api')
    
    @api.route('/users')
    def list_users():
        return 'Users list'
    
    @api.route('/users/<int:id>')
    def get_user(id):
        return f'User {id}'
    
    # Register blueprint
    app.register_blueprint(api)
    
    # Test blueprint routes
    view_func, args = app.match_request('/api/users', 'GET')
    assert view_func is not None, "Should match blueprint route"
    
    view_func, args = app.match_request('/api/users/123', 'GET')
    assert view_func is not None, "Should match blueprint route with variable"
    assert args == {'id': '123'}, f"Expected id=123, got {args}"
    
    print("✓ Blueprints work")


def test_template_rendering():
    """Test template rendering (fallback mode)."""
    print("Testing template rendering...")
    
    # Create templates directory and test template
    os.makedirs('templates', exist_ok=True)
    with open('templates/test.html', 'w') as f:
        f.write('<h1>Hello {{name}}!</h1>')
    
    app = Flask(__name__)
    
    with app.app_context():
        result = render_template('test.html', name='World')
        assert 'Hello World!' in result, f"Template should render with context, got: {result}"
    
    # Clean up
    os.remove('templates/test.html')
    os.rmdir('templates')
    
    print("✓ Template rendering works")


def test_wsgi_compliance():
    """Test WSGI compliance."""
    print("Testing WSGI compliance...")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello WSGI'
    
    # Mock WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'wsgi.input': StringIO('')
    }
    
    # Mock start_response
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    # Call WSGI app
    result = app(environ, start_response)
    response_body = b''.join(result)
    
    assert response_data['status'] == '200 OK', f"Expected 200 OK, got {response_data['status']}"
    assert response_body == b'Hello WSGI', f"Expected 'Hello WSGI', got {response_body}"
    assert any(h[0] == 'Content-Length' for h in response_data['headers']), "Should include Content-Length header"
    
    print("✓ WSGI compliance works")


def test_error_handling():
    """Test error handling."""
    print("Testing error handling...")
    
    app = Flask(__name__)
    
    @app.errorhandler(404)
    def not_found():
        return 'Custom 404', 404
    
    @app.route('/error')
    def error_route():
        raise ValueError("Test error")
    
    # Test 404 handling
    with app.app_context():
        response = app.handle_404()
        assert response.status_code == 404, "Should return 404 status"
        assert b'Custom 404' in response.data, "Should use custom 404 handler"
    
    # Test 500 handling
    with app.app_context():
        response = app.handle_500(ValueError("test"))
        assert response.status_code == 500, "Should return 500 status"
    
    print("✓ Error handling works")


def run_all_tests():
    """Run all tests."""
    print("Running FlaskFramework tests...\n")
    
    try:
        test_basic_routing()
        test_variable_segments()
        test_http_methods()
        test_request_object()
        test_response_object()
        test_application_context()
        test_blueprints()
        test_template_rendering()
        test_wsgi_compliance()
        test_error_handling()
        
        print("\n🎉 All tests passed! FlaskFramework is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
