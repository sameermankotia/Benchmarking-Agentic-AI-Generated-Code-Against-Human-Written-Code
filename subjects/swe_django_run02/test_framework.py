#!/usr/bin/env python3
"""
Test script to verify the Django framework implementation.
"""

import uuid
from djangoframework import (
    path, re_path, HttpRequest, HttpResponse, View, WSGIApplication
)


# Test views
def home_view(request):
    return HttpResponse("Welcome to Django Framework!")


def hello_view(request, name):
    return HttpResponse(f"Hello, {name}!")


def article_view(request, id):
    return HttpResponse(f"Article ID: {id} (type: {type(id).__name__})")


def category_view(request, category):
    return HttpResponse(f"Category: {category}")


def uuid_view(request, obj_id):
    return HttpResponse(f"UUID: {obj_id} (type: {type(obj_id).__name__})")


def path_view(request, filepath):
    return HttpResponse(f"File path: {filepath}")


def archive_view(request, year):
    return HttpResponse(f"Archive year: {year}")


# Test class-based view
class TestView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("GET method called")
    
    def post(self, request, *args, **kwargs):
        return HttpResponse("POST method called")


class GetOnlyView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Only GET is supported")


# URL patterns
urlpatterns = [
    path('', home_view),
    path('hello/<str:name>/', hello_view),
    path('article/<int:id>/', article_view),
    path('category/<slug:category>/', category_view),
    path('object/<uuid:obj_id>/', uuid_view),
    path('files/<path:filepath>/', path_view),
    re_path(r'^archive/(?P<year>[0-9]{4})/$', archive_view),
    path('test-view/', TestView.as_view()),
    path('get-only/', GetOnlyView.as_view()),
]


def create_test_environ(path='/', method='GET', query_string=''):
    """Create a test WSGI environ dict."""
    return {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'wsgi.input': None,
        'wsgi.errors': None,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'wsgi.url_scheme': 'http',
        'CONTENT_LENGTH': '0',
        'CONTENT_TYPE': '',
    }


def test_wsgi_compliance():
    """Test WSGI compliance."""
    print("Testing WSGI compliance...")
    
    app = WSGIApplication(urlpatterns)
    
    # Test basic request
    environ = create_test_environ('/')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    
    # Check that start_response was called
    assert len(responses) == 1, "start_response should be called once"
    
    status, headers = responses[0]
    assert status.startswith('200'), f"Expected 200 status, got {status}"
    
    # Check that result is iterable
    content = b''.join(result)
    assert b"Welcome to Django Framework!" in content
    
    print("✓ WSGI compliance test passed")


def test_url_patterns():
    """Test URL pattern matching."""
    print("Testing URL patterns...")
    
    app = WSGIApplication(urlpatterns)
    
    test_cases = [
        ('/', 'Welcome to Django Framework!'),
        ('/hello/world/', 'Hello, world!'),
        ('/article/123/', 'Article ID: 123'),
        ('/category/python-tips/', 'Category: python-tips'),
        ('/files/docs/readme.txt/', 'File path: docs/readme.txt'),
        ('/archive/2023/', 'Archive year: 2023'),
    ]
    
    for path, expected in test_cases:
        environ = create_test_environ(path)
        responses = []
        
        def start_response(status, headers):
            responses.append((status, headers))
        
        result = app(environ, start_response)
        content = b''.join(result).decode('utf-8')
        
        assert expected in content, f"Expected '{expected}' in response for {path}, got '{content}'"
        assert responses[0][0].startswith('200'), f"Expected 200 status for {path}"
    
    print("✓ URL pattern tests passed")


def test_404_handling():
    """Test 404 handling for unmatched URLs."""
    print("Testing 404 handling...")
    
    app = WSGIApplication(urlpatterns)
    environ = create_test_environ('/nonexistent/')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    
    status, headers = responses[0]
    assert status.startswith('404'), f"Expected 404 status, got {status}"
    
    print("✓ 404 handling test passed")


def test_class_based_views():
    """Test class-based view functionality."""
    print("Testing class-based views...")
    
    app = WSGIApplication(urlpatterns)
    
    # Test GET request
    environ = create_test_environ('/test-view/', 'GET')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'GET method called' in content
    assert responses[0][0].startswith('200')
    
    # Test POST request
    environ = create_test_environ('/test-view/', 'POST')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'POST method called' in content
    assert responses[0][0].startswith('200')
    
    print("✓ Class-based view tests passed")


def test_method_not_allowed():
    """Test 405 Method Not Allowed handling."""
    print("Testing 405 Method Not Allowed...")
    
    app = WSGIApplication(urlpatterns)
    
    # Test unsupported method on view that only supports GET
    environ = create_test_environ('/get-only/', 'POST')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    
    status, headers = responses[0]
    assert status.startswith('405'), f"Expected 405 status, got {status}"
    
    # Check for Allow header
    allow_header = None
    for name, value in headers:
        if name.lower() == 'allow':
            allow_header = value
            break
    
    assert allow_header is not None, "Allow header should be present"
    assert 'GET' in allow_header, "Allow header should include GET"
    assert 'HEAD' in allow_header, "Allow header should include HEAD (auto-generated)"
    
    print("✓ 405 Method Not Allowed test passed")


def test_head_requests():
    """Test HEAD request handling."""
    print("Testing HEAD requests...")
    
    app = WSGIApplication(urlpatterns)
    
    # Test HEAD request on view with GET method
    environ = create_test_environ('/get-only/', 'HEAD')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    status, headers = responses[0]
    assert status.startswith('200'), f"Expected 200 status for HEAD, got {status}"
    
    # HEAD responses should have empty body
    assert len(content) == 0, "HEAD response should have empty body"
    
    print("✓ HEAD request test passed")


def test_uuid_converter():
    """Test UUID converter."""
    print("Testing UUID converter...")
    
    app = WSGIApplication(urlpatterns)
    
    test_uuid = str(uuid.uuid4())
    environ = create_test_environ(f'/object/{test_uuid}/')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert test_uuid in content
    assert 'UUID' in content
    assert responses[0][0].startswith('200')
    
    print("✓ UUID converter test passed")


def run_all_tests():
    """Run all tests."""
    print("Running Django Framework tests...\n")
    
    try:
        test_wsgi_compliance()
        test_url_patterns()
        test_404_handling()
        test_class_based_views()
        test_method_not_allowed()
        test_head_requests()
        test_uuid_converter()
        
        print("\n🎉 All tests passed! The Django framework implementation is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
