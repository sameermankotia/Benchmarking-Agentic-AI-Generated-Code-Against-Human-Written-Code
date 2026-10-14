#!/usr/bin/env python3
"""
Comprehensive test script for the Django-style WSGI framework.
Tests all required functionality and WSGI compliance.
"""

import uuid
import json
from io import StringIO
from djangoframework import (
    path, re_path, HttpResponse, JsonResponse, View, 
    get_wsgi_application, Http404, Http405
)


# Test views
def home_view(request):
    return HttpResponse("Welcome to Django Framework!")


def user_detail(request, user_id):
    return HttpResponse(f"User ID: {user_id} (type: {type(user_id).__name__})")


def post_detail(request, slug):
    return HttpResponse(f"Post slug: {slug}")


def file_serve(request, filepath):
    return HttpResponse(f"File path: {filepath}")


def uuid_view(request, item_id):
    return HttpResponse(f"UUID: {item_id} (type: {type(item_id).__name__})")


def year_archive(request, year):
    return HttpResponse(f"Year: {year}")


def json_api(request):
    data = {
        'message': 'Hello API',
        'method': request.method,
        'path': request.path
    }
    return JsonResponse(data)


# Class-based view for testing
class TestView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("GET method")
    
    def post(self, request, *args, **kwargs):
        return HttpResponse("POST method")
    
    def put(self, request, *args, **kwargs):
        return HttpResponse("PUT method")


class HeadTestView(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse("GET content for HEAD test")
        response['X-Custom-Header'] = 'test-value'
        return response


# URL patterns
urlpatterns = [
    path('', home_view, name='home'),  # Empty string matches root after stripping /
    path('user/<int:user_id>/', user_detail, name='user_detail'),
    path('post/<slug:slug>/', post_detail, name='post_detail'),
    path('file/<path:filepath>/', file_serve, name='file_serve'),
    path('item/<uuid:item_id>/', uuid_view, name='uuid_view'),
    path('api/data/', json_api, name='json_api'),
    path('test-view/', TestView.as_view(), name='test_view'),
    path('head-test/', HeadTestView.as_view(), name='head_test'),
    re_path(r'^archive/(?P<year>[0-9]{4})/$', year_archive, name='year_archive'),
]


def create_wsgi_environ(method='GET', path='/', query_string='', 
                       content_type='', content_length=0, body=b''):
    """Create a WSGI environ dict for testing."""
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': content_type,
        'CONTENT_LENGTH': str(content_length),
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
    
    if body:
        from io import BytesIO
        environ['wsgi.input'] = BytesIO(body)
        environ['CONTENT_LENGTH'] = str(len(body))
    
    return environ


def test_wsgi_compliance():
    """Test WSGI compliance."""
    print("Testing WSGI compliance...")
    
    app = get_wsgi_application(urlpatterns)
    
    # Test basic WSGI call
    environ = create_wsgi_environ('GET', '/')
    
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


def test_url_resolution():
    """Test URL pattern matching and parameter conversion."""
    print("Testing URL resolution...")
    
    app = get_wsgi_application(urlpatterns)
    
    test_cases = [
        # (method, path, expected_content_substring)
        ('GET', '/', b'Welcome to Django Framework!'),
        ('GET', '/user/123/', b'User ID: 123'),
        ('GET', '/post/my-test-slug/', b'Post slug: my-test-slug'),
        ('GET', '/file/path/to/file.txt/', b'File path: path/to/file.txt'),
        ('GET', '/archive/2023/', b'Year: 2023'),
    ]
    
    for method, path, expected in test_cases:
        environ = create_wsgi_environ(method, path)
        
        responses = []
        def start_response(status, headers):
            responses.append((status, headers))
        
        result = app(environ, start_response)
        content = b''.join(result)
        
        assert expected in content, f"Expected {expected} in response for {path}, got {content}"
        assert responses[0][0].startswith('200'), f"Expected 200 for {path}, got {responses[0][0]}"
    
    print("✓ URL resolution test passed")


def test_type_converters():
    """Test that URL parameters are converted to correct Python types."""
    print("Testing type converters...")
    
    app = get_wsgi_application(urlpatterns)
    
    # Test integer conversion
    environ = create_wsgi_environ('GET', '/user/42/')
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    assert b'type: int' in content, "Integer parameter should be converted to int type"
    
    # Test UUID conversion
    test_uuid = str(uuid.uuid4())
    environ = create_wsgi_environ('GET', f'/item/{test_uuid}/')
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    assert b'type: UUID' in content, "UUID parameter should be converted to UUID type"
    
    print("✓ Type converter test passed")


def test_404_handling():
    """Test 404 Not Found responses."""
    print("Testing 404 handling...")
    
    app = get_wsgi_application(urlpatterns)
    
    environ = create_wsgi_environ('GET', '/nonexistent-path/')
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    assert responses[0][0].startswith('404'), f"Expected 404 status, got {responses[0][0]}"
    
    print("✓ 404 handling test passed")


def test_class_based_views():
    """Test class-based view functionality."""
    print("Testing class-based views...")
    
    app = get_wsgi_application(urlpatterns)
    
    # Test different HTTP methods
    methods = ['GET', 'POST', 'PUT']
    
    for method in methods:
        environ = create_wsgi_environ(method, '/test-view/')
        
        responses = []
        def start_response(status, headers):
            responses.append((status, headers))
        
        result = app(environ, start_response)
        content = b''.join(result)
        
        expected = f"{method} method".encode()
        assert expected in content, f"Expected {expected} for {method}, got {content}"
        assert responses[0][0].startswith('200'), f"Expected 200 for {method}, got {responses[0][0]}"
    
    print("✓ Class-based view test passed")


def test_method_not_allowed():
    """Test 405 Method Not Allowed responses."""
    print("Testing 405 Method Not Allowed...")
    
    app = get_wsgi_application(urlpatterns)
    
    # Try DELETE on a view that only supports GET, POST, PUT
    environ = create_wsgi_environ('DELETE', '/test-view/')
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    status, headers = responses[0]
    assert status.startswith('405'), f"Expected 405 status, got {status}"
    
    # Check for Allow header
    allow_header = None
    for name, value in headers:
        if name.lower() == 'allow':
            allow_header = value
            break
    
    assert allow_header is not None, "405 response should include Allow header"
    assert 'GET' in allow_header, "Allow header should include GET"
    assert 'POST' in allow_header, "Allow header should include POST"
    
    print("✓ 405 Method Not Allowed test passed")


def test_head_requests():
    """Test HEAD request handling."""
    print("Testing HEAD request handling...")
    
    app = get_wsgi_application(urlpatterns)
    
    # Test HEAD request on view with GET method
    environ = create_wsgi_environ('HEAD', '/head-test/')
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    status, headers = responses[0]
    assert status.startswith('200'), f"Expected 200 status for HEAD, got {status}"
    
    # HEAD response should have no content but same headers as GET
    assert len(content) == 0, "HEAD response should have empty content"
    
    # Check that custom header is present
    custom_header = None
    for name, value in headers:
        if name == 'X-Custom-Header':
            custom_header = value
            break
    
    assert custom_header == 'test-value', "HEAD response should include same headers as GET"
    
    print("✓ HEAD request test passed")


def test_json_response():
    """Test JSON response functionality."""
    print("Testing JSON responses...")
    
    app = get_wsgi_application(urlpatterns)
    
    environ = create_wsgi_environ('GET', '/api/data/')
    
    responses = []
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    status, headers = responses[0]
    assert status.startswith('200'), f"Expected 200 status, got {status}"
    
    # Check content type
    content_type = None
    for name, value in headers:
        if name.lower() == 'content-type':
            content_type = value
            break
    
    assert content_type == 'application/json', f"Expected JSON content type, got {content_type}"
    
    # Parse JSON content
    data = json.loads(content.decode('utf-8'))
    assert data['message'] == 'Hello API', "JSON response should contain expected data"
    assert data['method'] == 'GET', "JSON response should contain request method"
    assert data['path'] == '/api/data/', "JSON response should contain request path"
    
    print("✓ JSON response test passed")


def test_request_object():
    """Test HttpRequest object functionality."""
    print("Testing request object...")
    
    # This is tested implicitly in other tests, but we can add specific checks
    # The request object is created and passed to views, and we've verified
    # that it contains the correct method, path, etc. in the JSON API test
    
    print("✓ Request object test passed")


def run_all_tests():
    """Run all tests."""
    print("Running Django Framework Tests")
    print("=" * 40)
    
    try:
        test_wsgi_compliance()
        test_url_resolution()
        test_type_converters()
        test_404_handling()
        test_class_based_views()
        test_method_not_allowed()
        test_head_requests()
        test_json_response()
        test_request_object()
        
        print("=" * 40)
        print("✅ All tests passed!")
        print("The Django-style WSGI framework is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
