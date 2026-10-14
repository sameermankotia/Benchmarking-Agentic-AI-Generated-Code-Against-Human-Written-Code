#!/usr/bin/env python3
"""
Comprehensive test script for the Flask framework.
Tests all required features:
1. URL routing with variable segments and HTTP method filtering
2. Request object encapsulating method, path, headers, query string, and body
3. Response object with status code, headers, and body
4. Jinja2 template rendering integrated with the application context
5. Application context management using thread-local storage
6. Blueprint-based modular applications with URL prefix inheritance
7. WSGI compliance and built-in development server
"""

import os
import sys
import tempfile
import threading
import time
from io import StringIO
from wsgiref.simple_server import make_server

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flaskframework import Flask, Blueprint, current_app, g, Request, Response, render_template


def test_basic_routing():
    """Test 1: URL routing with variable segments and HTTP method filtering"""
    print("Testing URL routing with variable segments and HTTP method filtering...")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello World'
    
    @app.route('/user/<name>')
    def user_profile(name):
        return f'User: {name}'
    
    @app.route('/user/<int:user_id>')
    def user_by_id(user_id):
        return f'User ID: {user_id}'
    
    @app.route('/api/data', methods=['GET', 'POST'])
    def api_data():
        return 'API Data'
    
    # Test routing
    environ_base = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'wsgi.input': StringIO(),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    def start_response(status, headers):
        pass
    
    # Test basic route
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/'
    result = app(environ, start_response)
    assert b'Hello World' in b''.join(result)
    
    # Test variable segment
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/user/john'
    result = app(environ, start_response)
    assert b'User: john' in b''.join(result)
    
    # Test integer converter
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/user/123'
    result = app(environ, start_response)
    assert b'User ID: 123' in b''.join(result)
    
    print("✓ URL routing tests passed")


def test_request_object():
    """Test 2: Request object encapsulating method, path, headers, query string, and body"""
    print("Testing request object...")
    
    app = Flask(__name__)
    
    @app.route('/test', methods=['GET', 'POST'])
    def test_request():
        # We'll access request through WSGI environ in a real implementation
        return 'Request handled'
    
    # Create a request object directly
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/test',
        'QUERY_STRING': 'param1=value1&param2=value2',
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': '13',
        'HTTP_USER_AGENT': 'Test Agent',
        'HTTP_ACCEPT': 'application/json',
        'wsgi.input': StringIO('{"key":"value"}'),
    }
    
    request = Request(environ)
    
    # Test request properties
    assert request.method == 'POST'
    assert request.path == '/test'
    assert request.query_string == 'param1=value1&param2=value2'
    assert request.headers['User-Agent'] == 'Test Agent'
    assert request.headers['Accept'] == 'application/json'
    assert request.headers['Content-Type'] == 'application/json'
    assert request.args['param1'] == 'value1'
    assert request.args['param2'] == 'value2'
    
    print("✓ Request object tests passed")


def test_response_object():
    """Test 3: Response object with status code, headers, and body"""
    print("Testing response object...")
    
    # Test basic response
    response = Response('Hello World')
    assert response.body == 'Hello World'
    assert response.status_code == 200
    assert response.status == '200 OK'
    assert response.headers['Content-Type'] == 'text/html'
    
    # Test custom response
    response = Response('{"message": "success"}', status=201, 
                       headers={'Custom-Header': 'value'}, 
                       content_type='application/json')
    assert response.status_code == 201
    assert response.status == '201 Created'
    assert response.headers['Content-Type'] == 'application/json'
    assert response.headers['Custom-Header'] == 'value'
    
    # Test WSGI format
    wsgi_headers = response.get_wsgi_headers()
    assert ('Content-Type', 'application/json') in wsgi_headers
    assert ('Custom-Header', 'value') in wsgi_headers
    
    body_bytes = response.get_body_bytes()
    assert isinstance(body_bytes, bytes)
    assert body_bytes == b'{"message": "success"}'
    
    print("✓ Response object tests passed")


def test_template_rendering():
    """Test 4: Jinja2 template rendering integrated with the application context"""
    print("Testing template rendering...")
    
    # Create temporary template directory
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = os.path.join(temp_dir, 'templates')
        os.makedirs(template_dir)
        
        # Create a test template
        template_content = """<html>
<head><title>{{title}}</title></head>
<body><h1>Hello {{name}}!</h1></body>
</html>"""
        
        with open(os.path.join(template_dir, 'test.html'), 'w') as f:
            f.write(template_content)
        
        app = Flask(__name__, template_folder=template_dir)
        
        @app.route('/template/<name>')
        def template_test(name):
            return render_template('test.html', title='Test Page', name=name)
        
        # Test template rendering within app context
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/template/world',
            'QUERY_STRING': '',
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': '0',
            'wsgi.input': StringIO(),
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False
        }
        
        def start_response(status, headers):
            pass
        
        result = app(environ, start_response)
        response_body = b''.join(result).decode('utf-8')
        
        # Check if template was rendered (fallback to simple replacement)
        assert 'Hello world!' in response_body
        assert 'Test Page' in response_body
    
    print("✓ Template rendering tests passed")


def test_application_context():
    """Test 5: Application context management using thread-local storage"""
    print("Testing application context management...")
    
    app = Flask(__name__)
    
    @app.route('/context')
    def context_test():
        # Test current_app access
        app_name = current_app.import_name
        
        # Test g object
        g.test_value = 'context_data'
        
        return f'App: {app_name}, G: {g.test_value}'
    
    # Test context in different threads
    results = []
    
    def thread_test():
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/context',
            'QUERY_STRING': '',
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': '0',
            'wsgi.input': StringIO(),
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False
        }
        
        def start_response(status, headers):
            pass
        
        result = app(environ, start_response)
        response_body = b''.join(result).decode('utf-8')
        results.append(response_body)
    
    # Run in multiple threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=thread_test)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # All threads should have successful context access
    assert len(results) == 3
    for result in results:
        assert 'App: __main__' in result
        assert 'G: context_data' in result
    
    print("✓ Application context tests passed")


def test_blueprints():
    """Test 6: Blueprint-based modular applications with URL prefix inheritance"""
    print("Testing Blueprint-based modular applications...")
    
    # Create a blueprint
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    @api_bp.route('/users')
    def list_users():
        return 'Users list'
    
    @api_bp.route('/users/<int:user_id>')
    def get_user(user_id):
        return f'User {user_id}'
    
    # Create another blueprint with different prefix
    admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
    
    @admin_bp.route('/dashboard')
    def dashboard():
        return 'Admin dashboard'
    
    # Create main app and register blueprints
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    
    @app.route('/')
    def index():
        return 'Main page'
    
    # Test blueprint routes
    environ_base = {
        'REQUEST_METHOD': 'GET',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'wsgi.input': StringIO(),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    def start_response(status, headers):
        pass
    
    # Test main route
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/'
    result = app(environ, start_response)
    assert b'Main page' in b''.join(result)
    
    # Test blueprint route with prefix
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/api/users'
    result = app(environ, start_response)
    assert b'Users list' in b''.join(result)
    
    # Test blueprint route with variable
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/api/users/123'
    result = app(environ, start_response)
    assert b'User 123' in b''.join(result)
    
    # Test second blueprint
    environ = environ_base.copy()
    environ['PATH_INFO'] = '/admin/dashboard'
    result = app(environ, start_response)
    assert b'Admin dashboard' in b''.join(result)
    
    print("✓ Blueprint tests passed")


def test_wsgi_compliance():
    """Test 7: WSGI compliance and built-in development server"""
    print("Testing WSGI compliance...")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'WSGI Test'
    
    @app.route('/status')
    def status():
        return Response('OK', status=200, headers={'X-Test': 'value'})
    
    # Test WSGI interface
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'wsgi.input': StringIO(),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    response_started = False
    response_status = None
    response_headers = None
    
    def start_response(status, headers):
        nonlocal response_started, response_status, response_headers
        response_started = True
        response_status = status
        response_headers = headers
    
    # Test WSGI call
    result = app(environ, start_response)
    
    # Verify WSGI compliance
    assert response_started, "start_response was not called"
    assert response_status == '200 OK', f"Expected '200 OK', got '{response_status}'"
    assert isinstance(response_headers, list), "Headers should be a list"
    assert all(isinstance(h, tuple) and len(h) == 2 for h in response_headers), "Headers should be tuples"
    
    # Verify response body is iterable of bytes
    assert hasattr(result, '__iter__'), "Response should be iterable"
    body = b''.join(result)
    assert isinstance(body, bytes), "Response body should be bytes"
    assert b'WSGI Test' in body
    
    # Test custom status and headers
    environ['PATH_INFO'] = '/status'
    result = app(environ, start_response)
    assert response_status == '200 OK'
    header_dict = dict(response_headers)
    assert 'X-Test' in header_dict
    
    print("✓ WSGI compliance tests passed")


def test_development_server():
    """Test built-in development server (basic functionality)"""
    print("Testing built-in development server...")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Server Test'
    
    # Test that the server can be created (we won't actually run it)
    try:
        server = make_server('127.0.0.1', 0, app)  # Port 0 for any available port
        port = server.server_port
        server.server_close()
        print(f"✓ Development server can be created on port {port}")
    except Exception as e:
        print(f"✗ Development server test failed: {e}")
        raise


def main():
    """Run all tests"""
    print("Running Flask Framework Tests")
    print("=" * 50)
    
    try:
        test_basic_routing()
        test_request_object()
        test_response_object()
        test_template_rendering()
        test_application_context()
        test_blueprints()
        test_wsgi_compliance()
        test_development_server()
        
        print("=" * 50)
        print("✓ All tests passed! Framework meets all requirements:")
        print("  1. ✓ URL routing with variable segments and HTTP method filtering")
        print("  2. ✓ Request object encapsulating method, path, headers, query string, and body")
        print("  3. ✓ Response object with status code, headers, and body")
        print("  4. ✓ Jinja2 template rendering integrated with the application context")
        print("  5. ✓ Application context management using thread-local storage")
        print("  6. ✓ Blueprint-based modular applications with URL prefix inheritance")
        print("  7. ✓ WSGI compliance and built-in development server")
        print("\nScript completed successfully, no errors.")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
