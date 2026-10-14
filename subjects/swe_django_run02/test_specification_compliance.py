#!/usr/bin/env python3
"""
Test compliance with the Django-pair generation specification.

This test verifies that all requirements from the specification are met:
1. URL resolution from declared patterns (literal paths, variable segments with typed converters, regex patterns)
2. Request object encapsulating method, path, headers, query string, and body
3. View dispatch with 404 for unmatched patterns
4. Response handling with status code, headers, and body
5. Class-based views with HTTP verb dispatch, 405 handling, and HEAD from GET
"""

import uuid
import io
from wsgiref.validate import validator
from djangoframework import (
    path, re_path, include, HttpRequest, HttpResponse, View, WSGIApplication
)


def test_url_resolution():
    """Test requirement 1: URL resolution from declared patterns."""
    print("Testing URL resolution...")
    
    def literal_view(request):
        return HttpResponse("literal")
    
    def string_view(request, name):
        return HttpResponse(f"string:{name}")
    
    def int_view(request, id):
        return HttpResponse(f"int:{id}:{type(id).__name__}")
    
    def slug_view(request, slug):
        return HttpResponse(f"slug:{slug}")
    
    def uuid_view(request, uuid_param):
        return HttpResponse(f"uuid:{uuid_param}:{type(uuid_param).__name__}")
    
    def path_view(request, path_param):
        return HttpResponse(f"path:{path_param}")
    
    def regex_view(request, year, month):
        return HttpResponse(f"regex:{year}:{month}")
    
    urlpatterns = [
        path('literal/', literal_view),
        path('string/<str:name>/', string_view),
        path('int/<int:id>/', int_view),
        path('slug/<slug:slug>/', slug_view),
        path('uuid/<uuid:uuid_param>/', uuid_view),
        path('path/<path:path_param>/', path_view),
        re_path(r'^regex/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', regex_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    test_cases = [
        ('/literal/', 'literal'),
        ('/string/hello/', 'string:hello'),
        ('/int/123/', 'int:123:int'),
        ('/slug/hello-world_123/', 'slug:hello-world_123'),
        ('/path/docs/file.txt/', 'path:docs/file.txt'),
        ('/regex/2023/12/', 'regex:2023:12'),
    ]
    
    # Test UUID separately since we need a valid UUID
    test_uuid = str(uuid.uuid4())
    test_cases.append((f'/uuid/{test_uuid}/', f'uuid:{test_uuid}:UUID'))
    
    for path_info, expected in test_cases:
        environ = create_environ(path_info)
        responses = []
        
        def start_response(status, headers):
            responses.append((status, headers))
        
        result = app(environ, start_response)
        content = b''.join(result).decode('utf-8')
        
        assert expected in content, f"Expected '{expected}' in response for {path_info}, got '{content}'"
        assert responses[0][0].startswith('200'), f"Expected 200 status for {path_info}"
    
    print("✓ URL resolution test passed")


def test_request_object():
    """Test requirement 2: Request object encapsulation."""
    print("Testing request object...")
    
    def inspect_request(request):
        # Test that request has all required attributes
        assert hasattr(request, 'method'), "Request should have method attribute"
        assert hasattr(request, 'path'), "Request should have path attribute"
        assert hasattr(request, 'headers'), "Request should have headers attribute"
        assert hasattr(request, 'query_string'), "Request should have query_string attribute"
        assert hasattr(request, 'body'), "Request should have body attribute"
        assert hasattr(request, 'GET'), "Request should have GET attribute"
        assert hasattr(request, 'POST'), "Request should have POST attribute"
        
        return HttpResponse(f"method:{request.method},path:{request.path},qs:{request.query_string}")
    
    urlpatterns = [path('inspect/', inspect_request)]
    app = WSGIApplication(urlpatterns)
    
    # Test GET request with query string
    environ = create_environ('/inspect/', method='GET', query_string='foo=bar&baz=qux')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'method:GET' in content
    assert 'path:/inspect/' in content
    assert 'qs:foo=bar&baz=qux' in content
    
    print("✓ Request object test passed")


def test_view_dispatch_and_404():
    """Test requirement 3: View dispatch with 404 for unmatched patterns."""
    print("Testing view dispatch and 404 handling...")
    
    def test_view(request):
        return HttpResponse("found")
    
    urlpatterns = [path('exists/', test_view)]
    app = WSGIApplication(urlpatterns)
    
    # Test existing path
    environ = create_environ('/exists/')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'found' in content
    assert responses[0][0].startswith('200')
    
    # Test non-existing path (should return 404)
    environ = create_environ('/nonexistent/')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    
    assert responses[0][0].startswith('404'), "Should return 404 for unmatched patterns"
    
    print("✓ View dispatch and 404 test passed")


def test_response_handling():
    """Test requirement 4: Response handling with status, headers, and body."""
    print("Testing response handling...")
    
    def custom_response(request):
        response = HttpResponse("custom content", status=201)
        response.headers['Custom-Header'] = 'custom-value'
        return response
    
    urlpatterns = [path('custom/', custom_response)]
    app = WSGIApplication(urlpatterns)
    
    environ = create_environ('/custom/')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    # Check status
    assert responses[0][0].startswith('201'), "Should return custom status code"
    
    # Check headers
    headers_dict = dict(responses[0][1])
    assert 'Custom-Header' in headers_dict, "Should include custom headers"
    assert headers_dict['Custom-Header'] == 'custom-value'
    
    # Check body
    assert 'custom content' in content
    
    print("✓ Response handling test passed")


def test_class_based_views():
    """Test requirement 5: Class-based views with HTTP verb dispatch, 405, and HEAD from GET."""
    print("Testing class-based views...")
    
    class TestView(View):
        def get(self, request, *args, **kwargs):
            return HttpResponse("GET response")
        
        def post(self, request, *args, **kwargs):
            return HttpResponse("POST response")
    
    class GetOnlyView(View):
        def get(self, request, *args, **kwargs):
            return HttpResponse("GET only")
    
    urlpatterns = [
        path('cbv/', TestView.as_view()),
        path('get-only/', GetOnlyView.as_view()),
    ]
    app = WSGIApplication(urlpatterns)
    
    # Test GET method dispatch
    environ = create_environ('/cbv/', method='GET')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'GET response' in content
    assert responses[0][0].startswith('200')
    
    # Test POST method dispatch
    environ = create_environ('/cbv/', method='POST')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result).decode('utf-8')
    
    assert 'POST response' in content
    assert responses[0][0].startswith('200')
    
    # Test 405 Method Not Allowed for unsupported method
    environ = create_environ('/get-only/', method='POST')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    
    assert responses[0][0].startswith('405'), "Should return 405 for unsupported method"
    
    # Check Allow header
    headers_dict = dict(responses[0][1])
    assert 'Allow' in headers_dict, "405 response should include Allow header"
    assert 'GET' in headers_dict['Allow'], "Allow header should include GET"
    assert 'HEAD' in headers_dict['Allow'], "Allow header should include HEAD (auto-generated)"
    
    # Test HEAD request served from GET
    environ = create_environ('/get-only/', method='HEAD')
    responses = []
    
    def start_response(status, headers):
        responses.append((status, headers))
    
    result = app(environ, start_response)
    content = b''.join(result)
    
    assert responses[0][0].startswith('200'), "HEAD should return 200 when GET is available"
    assert len(content) == 0, "HEAD response should have empty body"
    
    print("✓ Class-based views test passed")


def test_wsgi_compliance():
    """Test WSGI compliance."""
    print("Testing WSGI compliance...")
    
    def simple_view(request):
        return HttpResponse("WSGI compliant")
    
    urlpatterns = [path('', simple_view)]
    app = WSGIApplication(urlpatterns)
    
    # Use wsgiref validator
    validated_app = validator(app)
    
    environ = create_environ('/')
    responses = []
    
    def start_response(status, headers, exc_info=None):
        responses.append((status, headers, exc_info))
    
    result = validated_app(environ, start_response)
    content = b''.join(result)
    
    assert len(responses) == 1, "start_response should be called exactly once"
    assert responses[0][0].startswith('200'), "Should return 200 status"
    assert b"WSGI compliant" in content
    
    print("✓ WSGI compliance test passed")


def test_include_functionality():
    """Test include functionality for organizing URL patterns."""
    print("Testing include functionality...")
    
    def view1(request):
        return HttpResponse("view1")
    
    def view2(request):
        return HttpResponse("view2")
    
    # Test include function
    included_patterns = include([
        path('view1/', view1),
        path('view2/', view2),
    ])
    
    urlpatterns = [
        path('', view1),
    ] + included_patterns
    
    app = WSGIApplication(urlpatterns)
    
    # Test that included patterns work
    for path_info, expected in [('/', 'view1'), ('/view1/', 'view1'), ('/view2/', 'view2')]:
        environ = create_environ(path_info)
        responses = []
        
        def start_response(status, headers):
            responses.append((status, headers))
        
        result = app(environ, start_response)
        content = b''.join(result).decode('utf-8')
        
        assert expected in content
        assert responses[0][0].startswith('200')
    
    print("✓ Include functionality test passed")


def create_environ(path_info='/', method='GET', query_string=''):
    """Create a test WSGI environ dict."""
    return {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path_info,
        'QUERY_STRING': query_string,
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


def run_all_tests():
    """Run all specification compliance tests."""
    print("Running Django Framework specification compliance tests...\n")
    
    try:
        test_url_resolution()
        test_request_object()
        test_view_dispatch_and_404()
        test_response_handling()
        test_class_based_views()
        test_wsgi_compliance()
        test_include_functionality()
        
        print("\n🎉 All specification compliance tests passed!")
        print("The Django Framework implementation meets all requirements:")
        print("1. ✓ URL resolution with literal paths, typed converters, and regex patterns")
        print("2. ✓ Request object with method, path, headers, query string, and body")
        print("3. ✓ View dispatch with 404 for unmatched patterns")
        print("4. ✓ Response handling with status codes, headers, and body")
        print("5. ✓ Class-based views with HTTP verb dispatch, 405 handling, and HEAD from GET")
        print("6. ✓ WSGI compliance verified")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Specification compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
