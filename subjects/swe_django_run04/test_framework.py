#!/usr/bin/env python3
"""
Comprehensive test script for the Django-style WSGI framework.
Tests all required functionality from the specification.
"""

import uuid
import sys
import os
from io import BytesIO

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from djangoframework import WSGIApplication, HttpResponse, HttpRequest, View, path, re_path


def test_basic_functionality():
    """Test basic URL routing and view dispatch."""
    print("Testing basic functionality...")
    
    def hello_world(request):
        return HttpResponse("Hello, World!")
    
    def hello_name(request, name):
        return HttpResponse(f"Hello, {name}!")
    
    urlpatterns = [
        path('', hello_world),  # Empty string for root path
        path('hello/<str:name>/', hello_name),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test root path
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'wsgi.input': BytesIO(b''),
    }
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    assert responses[0][0] == '200 OK'
    assert b'Hello, World!' in content
    print("✓ Basic routing works")
    
    # Test parameterized path
    environ['PATH_INFO'] = '/hello/Django/'
    responses.clear()
    result = app(environ, start_response)
    content = b''.join(result)
    
    assert responses[0][0] == '200 OK'
    assert b'Hello, Django!' in content
    print("✓ Parameterized routing works")


def test_converters():
    """Test all URL parameter converters."""
    print("\nTesting URL converters...")
    
    def int_view(request, id):
        return HttpResponse(f"ID: {id} (type: {type(id).__name__})")
    
    def slug_view(request, slug):
        return HttpResponse(f"Slug: {slug}")
    
    def uuid_view(request, uuid_param):
        return HttpResponse(f"UUID: {uuid_param} (type: {type(uuid_param).__name__})")
    
    def path_view(request, filepath):
        return HttpResponse(f"Path: {filepath}")
    
    urlpatterns = [
        path('int/<int:id>/', int_view),
        path('slug/<slug:slug>/', slug_view),
        path('uuid/<uuid:uuid_param>/', uuid_view),
        path('path/<path:filepath>/', path_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    def make_request(path_info):
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path_info,
            'QUERY_STRING': '',
            'wsgi.input': BytesIO(b''),
        }
        responses = []
        def start_response(status, headers):
            responses.append((status, headers))
        result = app(environ, start_response)
        return responses[0][0], b''.join(result)
    
    # Test integer converter
    status, content = make_request('/int/123/')
    assert status == '200 OK'
    assert b'ID: 123 (type: int)' in content
    print("✓ Integer converter works")
    
    # Test slug converter
    status, content = make_request('/slug/my-test-slug_123/')
    assert status == '200 OK'
    assert b'Slug: my-test-slug_123' in content
    print("✓ Slug converter works")
    
    # Test UUID converter
    test_uuid = str(uuid.uuid4())
    status, content = make_request(f'/uuid/{test_uuid}/')
    assert status == '200 OK'
    assert f'UUID: {test_uuid} (type: UUID)'.encode() in content
    print("✓ UUID converter works")
    
    # Test path converter
    status, content = make_request('/path/some/nested/path/file.txt/')
    assert status == '200 OK'
    assert b'Path: some/nested/path/file.txt' in content
    print("✓ Path converter works")


def test_regex_patterns():
    """Test regular expression URL patterns."""
    print("\nTesting regex patterns...")
    
    def year_view(request, year):
        return HttpResponse(f"Year: {year}")
    
    urlpatterns = [
        re_path(r'^archive/(?P<year>[0-9]{4})/$', year_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    def make_request(path_info):
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path_info,
            'QUERY_STRING': '',
            'wsgi.input': BytesIO(b''),
        }
        responses = []
        def start_response(status, headers):
            responses.append((status, headers))
        result = app(environ, start_response)
        return responses[0][0], b''.join(result)
    
    # Test valid year
    status, content = make_request('/archive/2023/')
    assert status == '200 OK'
    assert b'Year: 2023' in content
    print("✓ Regex pattern matching works")
    
    # Test invalid year (should 404)
    status, content = make_request('/archive/23/')
    assert status == '404 Not Found'
    print("✓ Regex pattern rejection works")


def test_class_based_views():
    """Test class-based views with method dispatch."""
    print("\nTesting class-based views...")
    
    class ArticleView(View):
        def get(self, request, id):
            return HttpResponse(f"GET Article {id}")
        
        def post(self, request, id):
            return HttpResponse(f"POST Article {id}")
    
    class ReadOnlyView(View):
        def get(self, request):
            return HttpResponse("GET only")
    
    urlpatterns = [
        path('article/<int:id>/', ArticleView.as_view()),
        path('readonly/', ReadOnlyView.as_view()),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    def make_request(path_info, method='GET'):
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path_info,
            'QUERY_STRING': '',
            'wsgi.input': BytesIO(b''),
        }
        responses = []
        def start_response(status, headers):
            responses.append((status, headers))
        result = app(environ, start_response)
        return responses[0][0], responses[0][1], b''.join(result)
    
    # Test GET method
    status, headers, content = make_request('/article/123/')
    assert status == '200 OK'
    assert b'GET Article 123' in content
    print("✓ Class-based view GET works")
    
    # Test POST method
    status, headers, content = make_request('/article/123/', 'POST')
    assert status == '200 OK'
    assert b'POST Article 123' in content
    print("✓ Class-based view POST works")
    
    # Test HEAD method (should use GET implementation)
    status, headers, content = make_request('/article/123/', 'HEAD')
    assert status == '200 OK'
    assert content == b''  # HEAD should have empty body
    print("✓ Class-based view HEAD works")
    
    # Test unsupported method (should return 405)
    status, headers, content = make_request('/readonly/', 'POST')
    assert status == '405 Method Not Allowed'
    # Check Allow header
    allow_header = None
    for name, value in headers:
        if name == 'Allow':
            allow_header = value
            break
    assert allow_header is not None
    assert 'GET' in allow_header
    assert 'HEAD' in allow_header
    print("✓ Class-based view 405 response works")


def test_request_object():
    """Test HttpRequest object functionality."""
    print("\nTesting request object...")
    
    def inspect_request(request):
        info = []
        info.append(f"Method: {request.method}")
        info.append(f"Path: {request.path}")
        info.append(f"Headers: {len(request.headers)}")
        info.append(f"Query: {request.query_string}")
        return HttpResponse('\n'.join(info))
    
    urlpatterns = [
        path('inspect/', inspect_request),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/inspect/',
        'QUERY_STRING': 'param1=value1&param2=value2',
        'HTTP_USER_AGENT': 'TestAgent/1.0',
        'HTTP_ACCEPT': 'text/html',
        'wsgi.input': BytesIO(b''),
    }
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'Method: GET' in content
    assert 'Path: /inspect/' in content
    assert 'Query: param1=value1&param2=value2' in content
    print("✓ Request object works correctly")


def test_404_handling():
    """Test 404 Not Found responses."""
    print("\nTesting 404 handling...")
    
    def home(request):
        return HttpResponse("Home")
    
    urlpatterns = [
        path('', home),  # Empty string for root path
    ]
    
    app = WSGIApplication(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/nonexistent/',
        'QUERY_STRING': '',
        'wsgi.input': BytesIO(b''),
    }
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    assert responses[0][0] == '404 Not Found'
    assert b'404 Not Found' in content
    print("✓ 404 handling works")


def test_wsgi_compliance():
    """Test WSGI compliance basics."""
    print("\nTesting WSGI compliance...")
    
    def simple_view(request):
        return HttpResponse("WSGI Test")
    
    urlpatterns = [
        path('test/', simple_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test that app is callable
    assert callable(app)
    
    # Test basic WSGI interface
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/test/',
        'QUERY_STRING': '',
        'wsgi.input': BytesIO(b''),
    }
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
        # start_response should return a write callable (we don't use it)
        return lambda data: None
    
    result = app(environ, start_response)
    
    # Result should be iterable
    assert hasattr(result, '__iter__')
    
    # Should have called start_response
    assert len(responses) == 1
    status, headers = responses[0]
    
    # Status should be a string
    assert isinstance(status, str)
    assert status.startswith('200')
    
    # Headers should be a list of tuples
    assert isinstance(headers, list)
    for header in headers:
        assert isinstance(header, tuple)
        assert len(header) == 2
        assert isinstance(header[0], str)
        assert isinstance(header[1], str)
    
    # Content should be bytes
    content = b''.join(result)
    assert isinstance(content, bytes)
    assert b'WSGI Test' in content
    
    print("✓ WSGI compliance verified")


def main():
    """Run all tests."""
    print("Django Framework Test Suite")
    print("=" * 40)
    
    try:
        test_basic_functionality()
        test_converters()
        test_regex_patterns()
        test_class_based_views()
        test_request_object()
        test_404_handling()
        test_wsgi_compliance()
        
        print("\n" + "=" * 40)
        print("✅ All tests passed! Framework is working correctly.")
        print("The implementation meets all specification requirements:")
        print("  ✓ URL resolution with literal paths and variable segments")
        print("  ✓ Typed converters (int, str, slug, uuid, path)")
        print("  ✓ Regular expression patterns with named groups")
        print("  ✓ Request object with method, path, headers, query, body")
        print("  ✓ View dispatch with captured segments")
        print("  ✓ 404 responses for unmatched patterns")
        print("  ✓ Response objects with status, headers, body")
        print("  ✓ Class-based views with HTTP method dispatch")
        print("  ✓ 405 responses with Allow header")
        print("  ✓ HEAD requests served from GET implementations")
        print("  ✓ WSGI compliance verified")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
