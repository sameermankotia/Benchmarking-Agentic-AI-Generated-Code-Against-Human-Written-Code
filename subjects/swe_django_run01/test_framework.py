#!/usr/bin/env python3
"""
Comprehensive test script for the Django-style framework.
Tests all required functionality from the specification.
"""

import sys
import uuid
from io import StringIO
from djangoframework import (
    WSGIApplication, HttpResponse, HttpResponseNotFound, HttpResponseNotAllowed,
    View, path, re_path, HttpRequest
)


def test_literal_paths():
    """Test literal path matching."""
    print("Testing literal paths...")
    
    def home_view(request):
        return HttpResponse("Home")
    
    def about_view(request):
        return HttpResponse("About")
    
    urlpatterns = [
        path('/', home_view),
        path('/about/', about_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test home page
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    assert b'Home' in b''.join(result)
    assert '200 OK' in response_data[0]
    
    # Test about page
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/about/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    assert b'About' in b''.join(result)
    assert '200 OK' in response_data[0]
    
    print("✓ Literal paths working")


def test_typed_converters():
    """Test variable segments with typed converters."""
    print("Testing typed converters...")
    
    def user_view(request, user_id):
        return HttpResponse(f"User {user_id} (type: {type(user_id).__name__})")
    
    def article_view(request, title):
        return HttpResponse(f"Article: {title}")
    
    def file_view(request, filepath):
        return HttpResponse(f"File: {filepath}")
    
    def uuid_view(request, pk):
        return HttpResponse(f"UUID: {pk} (type: {type(pk).__name__})")
    
    def slug_view(request, slug):
        return HttpResponse(f"Slug: {slug}")
    
    urlpatterns = [
        path('/user/<int:user_id>/', user_view),
        path('/article/<str:title>/', article_view),
        path('/files/<path:filepath>/', file_view),
        path('/item/<uuid:pk>/', uuid_view),
        path('/blog/<slug:slug>/', slug_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test integer converter
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/user/123/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'User 123 (type: int)' in content
    
    # Test string converter
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/article/hello/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'Article: hello' in content
    
    # Test path converter
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/files/docs/readme.txt/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'File: docs/readme.txt' in content
    
    # Test UUID converter
    test_uuid = str(uuid.uuid4())
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': f'/item/{test_uuid}/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert f'UUID: {test_uuid} (type: UUID)' in content
    
    # Test slug converter
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/blog/my-blog-post/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'Slug: my-blog-post' in content
    
    print("✓ Typed converters working")


def test_regex_patterns():
    """Test regular expression patterns with named groups."""
    print("Testing regex patterns...")
    
    def year_view(request, year):
        return HttpResponse(f"Year: {year}")
    
    def date_view(request, year, month, day):
        return HttpResponse(f"Date: {year}-{month}-{day}")
    
    urlpatterns = [
        re_path(r'^/archive/(?P<year>[0-9]{4})/$', year_view),
        re_path(r'^/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', date_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test year pattern
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/archive/2023/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'Year: 2023' in content
    
    # Test full date pattern
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/archive/2023/12/25/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'Date: 2023-12-25' in content
    
    print("✓ Regex patterns working")


def test_request_object():
    """Test request object functionality."""
    print("Testing request object...")
    
    def test_view(request):
        info = []
        info.append(f"Method: {request.method}")
        info.append(f"Path: {request.path}")
        info.append(f"Query params: {dict(request.GET)}")
        info.append(f"Content-Type: {request.META.get('Content-Type', 'None')}")
        return HttpResponse("; ".join(info))
    
    urlpatterns = [
        path('/test/', test_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test GET request with query string
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/test/',
        'QUERY_STRING': 'name=john&age=30',
        'CONTENT_TYPE': 'application/json',
        'HTTP_USER_AGENT': 'TestAgent/1.0'
    }
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    content = b''.join(result).decode()
    
    assert 'Method: GET' in content
    assert 'Path: /test/' in content
    assert "'name': 'john'" in content
    assert "'age': '30'" in content
    assert 'Content-Type: application/json' in content
    
    print("✓ Request object working")


def test_404_handling():
    """Test 404 Not Found for unmatched patterns."""
    print("Testing 404 handling...")
    
    def home_view(request):
        return HttpResponse("Home")
    
    urlpatterns = [
        path('/', home_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test non-existent path
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/nonexistent/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    assert '404 Not Found' in response_data[0]
    
    print("✓ 404 handling working")


def test_class_based_views():
    """Test class-based view functionality."""
    print("Testing class-based views...")
    
    class TestView(View):
        def get(self, request, item_id):
            return HttpResponse(f"GET item {item_id}")
        
        def post(self, request, item_id):
            return HttpResponse(f"POST item {item_id}")
    
    urlpatterns = [
        path('/item/<int:item_id>/', TestView.as_view()),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test GET method
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/item/123/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'GET item 123' in content
    assert '200 OK' in response_data[0]
    
    # Test POST method
    environ = {'REQUEST_METHOD': 'POST', 'PATH_INFO': '/item/123/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'POST item 123' in content
    assert '200 OK' in response_data[0]
    
    # Test unsupported method (PUT)
    environ = {'REQUEST_METHOD': 'PUT', 'PATH_INFO': '/item/123/', 'QUERY_STRING': ''}
    response_data = []
    result = app(environ, start_response)
    assert '405 Method Not Allowed' in response_data[0]
    
    # Check Allow header
    headers = dict(response_data[1])
    assert 'Allow' in headers
    allowed_methods = headers['Allow'].split(', ')
    assert 'GET' in allowed_methods
    assert 'POST' in allowed_methods
    assert 'HEAD' in allowed_methods  # Should be automatically added
    
    print("✓ Class-based views working")


def test_head_requests():
    """Test HEAD request handling."""
    print("Testing HEAD requests...")
    
    class TestView(View):
        def get(self, request):
            return HttpResponse("GET response body")
    
    urlpatterns = [
        path('/test/', TestView.as_view()),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test HEAD request (should use GET handler)
    environ = {'REQUEST_METHOD': 'HEAD', 'PATH_INFO': '/test/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    content = b''.join(result).decode()
    assert 'GET response body' in content  # HEAD uses GET implementation
    assert '200 OK' in response_data[0]
    
    print("✓ HEAD requests working")


def test_options_requests():
    """Test OPTIONS request handling."""
    print("Testing OPTIONS requests...")
    
    class TestView(View):
        def get(self, request):
            return HttpResponse("GET")
        
        def post(self, request):
            return HttpResponse("POST")
    
    urlpatterns = [
        path('/test/', TestView.as_view()),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test OPTIONS request
    environ = {'REQUEST_METHOD': 'OPTIONS', 'PATH_INFO': '/test/', 'QUERY_STRING': ''}
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    assert '200 OK' in response_data[0]
    
    # Check Allow header
    headers = dict(response_data[1])
    assert 'Allow' in headers
    allowed_methods = headers['Allow'].split(', ')
    assert 'GET' in allowed_methods
    assert 'POST' in allowed_methods
    assert 'HEAD' in allowed_methods
    assert 'OPTIONS' in allowed_methods
    
    print("✓ OPTIONS requests working")


def test_wsgi_compliance():
    """Test basic WSGI compliance."""
    print("Testing WSGI compliance...")
    
    def simple_view(request):
        return HttpResponse("Hello WSGI")
    
    urlpatterns = [
        path('/', simple_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test that app is callable
    assert callable(app)
    
    # Test basic WSGI call
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': StringIO(),
        'wsgi.errors': StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
        return lambda x: None  # write function (not used)
    
    result = app(environ, start_response)
    
    # Check that result is iterable
    assert hasattr(result, '__iter__')
    
    # Check that start_response was called with proper arguments
    assert len(response_data) >= 2
    assert isinstance(response_data[0], str)  # status
    assert isinstance(response_data[1], list)  # headers
    
    # Check response content
    content = b''.join(result)
    assert b'Hello WSGI' in content
    
    print("✓ WSGI compliance working")


def main():
    """Run all tests."""
    print("Running Django Framework Tests")
    print("=" * 40)
    
    try:
        test_literal_paths()
        test_typed_converters()
        test_regex_patterns()
        test_request_object()
        test_404_handling()
        test_class_based_views()
        test_head_requests()
        test_options_requests()
        test_wsgi_compliance()
        
        print("=" * 40)
        print("✅ All tests passed! Framework is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
