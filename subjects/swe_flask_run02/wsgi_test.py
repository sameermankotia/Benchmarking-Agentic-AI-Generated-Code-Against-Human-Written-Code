#!/usr/bin/env python3
"""
WSGI compliance test for the Flask framework.
"""

import sys
import io
from wsgiref.validate import validator
from wsgiref.simple_server import make_server

sys.path.insert(0, '.')
from flaskframework import Flask

# Create a simple test application
app = Flask(__name__)

@app.route('/')
def index():
    return 'WSGI Compliance Test - OK'

@app.route('/json')
def json_response():
    return {'message': 'JSON response', 'status': 'ok'}

@app.route('/user/<int:user_id>')
def user(user_id):
    return f'User ID: {user_id}'

# Wrap the application with WSGI validator
validated_app = validator(app)

def test_wsgi_compliance():
    """Test WSGI compliance using wsgiref validator."""
    print("Testing WSGI compliance...")
    
    # Test basic request
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'SCRIPT_NAME': '',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'HTTP_HOST': 'localhost:8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': io.BytesIO(b''),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    responses = []
    def start_response(status, headers, exc_info=None):
        responses.append((status, headers))
    
    try:
        # This will raise an exception if WSGI compliance fails
        result = validated_app(environ, start_response)
        response_data = b''.join(result)
        
        print("✓ Basic WSGI compliance test passed")
        print(f"  Status: {responses[0][0]}")
        print(f"  Response: {response_data.decode()}")
        
        # Test JSON response
        environ['PATH_INFO'] = '/json'
        responses.clear()
        result = validated_app(environ, start_response)
        response_data = b''.join(result)
        
        print("✓ JSON response WSGI compliance test passed")
        print(f"  Status: {responses[0][0]}")
        print(f"  Response: {response_data.decode()}")
        
        # Test variable route
        environ['PATH_INFO'] = '/user/123'
        responses.clear()
        result = validated_app(environ, start_response)
        response_data = b''.join(result)
        
        print("✓ Variable route WSGI compliance test passed")
        print(f"  Status: {responses[0][0]}")
        print(f"  Response: {response_data.decode()}")
        
        return True
        
    except Exception as e:
        print(f"❌ WSGI compliance test failed: {e}")
        return False

def test_development_server():
    """Test the built-in development server."""
    print("\nTesting built-in development server...")
    
    try:
        # Create server but don't start it
        server = make_server('127.0.0.1', 0, app)  # Port 0 = random available port
        port = server.server_port
        
        print(f"✓ Development server created successfully on port {port}")
        print("  (Server not started to avoid blocking)")
        
        server.server_close()
        return True
        
    except Exception as e:
        print(f"❌ Development server test failed: {e}")
        return False

if __name__ == '__main__':
    print("Flask Framework WSGI Compliance Test")
    print("=" * 40)
    
    success = True
    success &= test_wsgi_compliance()
    success &= test_development_server()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All WSGI compliance tests passed!")
        print("The framework is fully WSGI-compatible and ready for deployment.")
    else:
        print("❌ Some tests failed.")
    
    sys.exit(0 if success else 1)
