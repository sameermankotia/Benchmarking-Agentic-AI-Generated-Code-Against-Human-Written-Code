#!/usr/bin/env python3
"""
WSGI compliance test for the Django-style framework.
"""

from io import StringIO
from djangoframework import WSGIApplication, HttpResponse, path


def simple_view(request):
    """Simple view for testing."""
    return HttpResponse("Hello WSGI World!")


def test_wsgi_compliance():
    """Test WSGI compliance according to PEP 3333."""
    print("Testing WSGI compliance...")
    
    urlpatterns = [
        path('/', simple_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Create a proper WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': StringIO(),
        'wsgi.errors': StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Test that the application is callable
    assert callable(app), "Application must be callable"
    
    # Test start_response callback
    response_started = []
    def start_response(status, response_headers, exc_info=None):
        """WSGI start_response callable."""
        response_started.append((status, response_headers, exc_info))
        return lambda data: None  # write callable (not used in this test)
    
    # Call the application
    result = app(environ, start_response)
    
    # Test that start_response was called
    assert len(response_started) == 1, "start_response must be called exactly once"
    
    status, headers, exc_info = response_started[0]
    
    # Test status format
    assert isinstance(status, str), "Status must be a string"
    assert status.startswith('200'), "Status should be 200 OK"
    assert 'OK' in status, "Status should contain reason phrase"
    
    # Test headers format
    assert isinstance(headers, list), "Headers must be a list"
    for header in headers:
        assert isinstance(header, tuple), "Each header must be a tuple"
        assert len(header) == 2, "Each header must have exactly 2 elements"
        assert isinstance(header[0], str), "Header name must be a string"
        assert isinstance(header[1], str), "Header value must be a string"
    
    # Test that result is iterable
    assert hasattr(result, '__iter__'), "Result must be iterable"
    
    # Test that result yields bytes
    content = b''.join(result)
    assert isinstance(content, bytes), "Result must yield bytes"
    assert b'Hello WSGI World!' in content, "Content should match expected response"
    
    # Test Content-Type header is present
    header_dict = dict(headers)
    assert 'Content-Type' in header_dict, "Content-Type header should be present"
    
    print("✓ Basic WSGI compliance verified")
    
    # Test 404 response
    environ['PATH_INFO'] = '/nonexistent/'
    response_started.clear()
    result = app(environ, start_response)
    
    status, headers, exc_info = response_started[0]
    assert status.startswith('404'), "Should return 404 for non-existent paths"
    
    print("✓ 404 handling WSGI compliant")
    
    # Test with query string
    environ['PATH_INFO'] = '/'
    environ['QUERY_STRING'] = 'test=value'
    response_started.clear()
    result = app(environ, start_response)
    
    status, headers, exc_info = response_started[0]
    assert status.startswith('200'), "Should handle query strings correctly"
    
    print("✓ Query string handling WSGI compliant")
    
    print("✅ All WSGI compliance tests passed!")


if __name__ == '__main__':
    test_wsgi_compliance()
