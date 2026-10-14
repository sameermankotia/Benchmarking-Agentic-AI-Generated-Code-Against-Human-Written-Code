#!/usr/bin/env python3
"""
WSGI compliance test for Django Framework.
"""

import io
from wsgiref.validate import validator
from djangoframework import path, HttpResponse, WSGIApplication


def simple_view(request):
    """Simple test view."""
    return HttpResponse("Hello, WSGI!")


def test_wsgi_compliance():
    """Test WSGI compliance using wsgiref.validate."""
    print("Testing WSGI compliance with wsgiref.validate...")
    
    # Create application
    urlpatterns = [
        path('', simple_view),
        path('test/', simple_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Wrap with validator
    validated_app = validator(app)
    
    # Create test environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': io.BytesIO(b''),
        'wsgi.errors': io.StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Test the application
    responses = []
    
    def start_response(status, headers, exc_info=None):
        responses.append((status, headers, exc_info))
    
    try:
        result = validated_app(environ, start_response)
        
        # Consume the result
        content = b''.join(result)
        
        # Check response
        assert len(responses) == 1, "start_response should be called exactly once"
        status, headers, exc_info = responses[0]
        
        assert status.startswith('200'), f"Expected 200 status, got {status}"
        assert b"Hello, WSGI!" in content, f"Expected content not found: {content}"
        
        print("✓ WSGI compliance test passed!")
        return True
        
    except Exception as e:
        print(f"❌ WSGI compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wsgi_error_handling():
    """Test WSGI error handling."""
    print("Testing WSGI error handling...")
    
    def error_view(request):
        raise ValueError("Test error")
    
    urlpatterns = [
        path('error/', error_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    validated_app = validator(app)
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/error/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '0',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': io.BytesIO(b''),
        'wsgi.errors': io.StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    responses = []
    
    def start_response(status, headers, exc_info=None):
        responses.append((status, headers, exc_info))
    
    try:
        result = validated_app(environ, start_response)
        content = b''.join(result)
        
        assert len(responses) == 1
        status, headers, exc_info = responses[0]
        
        assert status.startswith('500'), f"Expected 500 status for error, got {status}"
        
        print("✓ WSGI error handling test passed!")
        return True
        
    except Exception as e:
        print(f"❌ WSGI error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running WSGI compliance tests...\n")
    
    success1 = test_wsgi_compliance()
    success2 = test_wsgi_error_handling()
    
    if success1 and success2:
        print("\n🎉 All WSGI compliance tests passed!")
        exit(0)
    else:
        print("\n❌ Some WSGI compliance tests failed!")
        exit(1)
