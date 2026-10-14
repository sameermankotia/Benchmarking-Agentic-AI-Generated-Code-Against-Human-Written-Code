#!/usr/bin/env python3
"""
WSGI compliance test using wsgiref validator.
"""

import io
import sys
from wsgiref.validate import validator
from flaskframework import Flask


def test_wsgi_compliance_with_validator():
    """Test WSGI compliance using the official wsgiref validator."""
    print("Testing WSGI compliance with wsgiref validator...")
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello, WSGI Validator!'
    
    @app.route('/json')
    def json_response():
        return {'message': 'JSON response', 'status': 'ok'}
    
    # Wrap the app with the WSGI validator
    validated_app = validator(app)
    
    # Test basic GET request
    environ = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'wsgi.input': io.BytesIO(b''),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'HTTP_HOST': 'localhost:8000',
        'HTTP_USER_AGENT': 'WSGI-Test/1.0',
    }
    
    responses = []
    def start_response(status, headers, exc_info=None):
        responses.append((status, headers, exc_info))
    
    try:
        # Test the validated app
        result = list(validated_app(environ, start_response))
        
        # Verify response
        assert len(responses) == 1, "start_response should be called exactly once"
        status, headers, exc_info = responses[0]
        assert status == '200 OK', f"Expected '200 OK', got '{status}'"
        assert exc_info is None, "No exception info should be present"
        assert len(result) == 1, "Response should be iterable with one item"
        assert b'Hello, WSGI Validator!' in result[0], "Response body should contain expected content"
        
        print("✓ Basic GET request passed WSGI validation")
        
        # Test JSON response
        environ['PATH_INFO'] = '/json'
        responses = []
        result = list(validated_app(environ, start_response))
        
        status, headers, exc_info = responses[0]
        assert status == '200 OK'
        header_dict = dict(headers)
        assert 'application/json' in header_dict.get('Content-Type', '')
        
        print("✓ JSON response passed WSGI validation")
        
        print("✓ All WSGI compliance tests passed!")
        
    except Exception as e:
        print(f"✗ WSGI compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    test_wsgi_compliance_with_validator()
    print("\nThe Flask framework is fully WSGI-compliant! 🎉")
