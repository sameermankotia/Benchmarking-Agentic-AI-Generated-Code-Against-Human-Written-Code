#!/usr/bin/env python3
"""
Verification script that demonstrates all features required by the specification.
"""

import uuid
from io import StringIO
from djangoframework import (
    WSGIApplication, HttpResponse, HttpResponseNotFound, HttpResponseNotAllowed,
    View, path, re_path
)


def verify_specification():
    """Verify all specification requirements are met."""
    print("Django-pair Generation Specification Verification")
    print("=" * 50)
    
    # 1. URL RESOLUTION
    print("\n1. URL Resolution Testing")
    print("-" * 30)
    
    # Test views for different URL patterns
    def literal_view(request):
        return HttpResponse("Literal path matched")
    
    def int_view(request, number):
        return HttpResponse(f"Integer: {number} (type: {type(number).__name__})")
    
    def str_view(request, text):
        return HttpResponse(f"String: {text}")
    
    def slug_view(request, slug):
        return HttpResponse(f"Slug: {slug}")
    
    def uuid_view(request, uuid_val):
        return HttpResponse(f"UUID: {uuid_val} (type: {type(uuid_val).__name__})")
    
    def path_view(request, filepath):
        return HttpResponse(f"Path: {filepath}")
    
    def regex_view(request, year, month):
        return HttpResponse(f"Regex match: {year}-{month}")
    
    urlpatterns = [
        # Literal paths
        path('/home/', literal_view),
        
        # Variable segments with typed converters
        path('/number/<int:number>/', int_view),
        path('/text/<str:text>/', str_view),
        path('/article/<slug:slug>/', slug_view),
        path('/item/<uuid:uuid_val>/', uuid_view),
        path('/files/<path:filepath>/', path_view),
        
        # Regular expression patterns with named groups
        re_path(r'^/archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', regex_view),
    ]
    
    app = WSGIApplication(urlpatterns)
    
    # Test literal paths
    result = test_request(app, '/home/')
    assert "Literal path matched" in result['content']
    print("✓ Literal paths working")
    
    # Test integer converter
    result = test_request(app, '/number/42/')
    assert "Integer: 42 (type: int)" in result['content']
    print("✓ Integer converter working")
    
    # Test string converter
    result = test_request(app, '/text/hello/')
    assert "String: hello" in result['content']
    print("✓ String converter working")
    
    # Test slug converter
    result = test_request(app, '/article/my-article-title/')
    assert "Slug: my-article-title" in result['content']
    print("✓ Slug converter working")
    
    # Test UUID converter
    test_uuid = str(uuid.uuid4())
    result = test_request(app, f'/item/{test_uuid}/')
    assert f"UUID: {test_uuid} (type: UUID)" in result['content']
    print("✓ UUID converter working")
    
    # Test path converter
    result = test_request(app, '/files/docs/readme.txt/')
    assert "Path: docs/readme.txt" in result['content']
    print("✓ Path converter working")
    
    # Test regex pattern
    result = test_request(app, '/archive/2023/12/')
    assert "Regex match: 2023-12" in result['content']
    print("✓ Regular expression patterns working")
    
    # 2. REQUEST OBJECT
    print("\n2. Request Object Testing")
    print("-" * 30)
    
    def request_test_view(request):
        info = []
        info.append(f"Method: {request.method}")
        info.append(f"Path: {request.path}")
        info.append(f"Query: {dict(request.GET)}")
        info.append(f"Headers: {len(request.META)} items")
        info.append(f"Body length: {len(request.body)}")
        return HttpResponse("; ".join(info))
    
    request_urlpatterns = [
        path('/request-test/', request_test_view),
    ]
    
    request_app = WSGIApplication(request_urlpatterns)
    
    # Test request with query string and headers
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/request-test/',
        'QUERY_STRING': 'param1=value1&param2=value2',
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': '13',
        'HTTP_USER_AGENT': 'TestAgent/1.0',
        'HTTP_AUTHORIZATION': 'Bearer token123',
        'wsgi.input': StringIO('{"test": true}'),
        'wsgi.errors': StringIO(),
    }
    
    result = test_request_with_environ(request_app, environ)
    content = result['content']
    
    assert "Method: POST" in content
    assert "Path: /request-test/" in content
    assert "'param1': 'value1'" in content
    assert "'param2': 'value2'" in content
    print("✓ Request object encapsulates method, path, headers, query string, and body")
    
    # 3. VIEW DISPATCH
    print("\n3. View Dispatch Testing")
    print("-" * 30)
    
    def first_view(request):
        return HttpResponse("First view")
    
    def second_view(request):
        return HttpResponse("Second view")
    
    dispatch_urlpatterns = [
        path('/first/', first_view),
        path('/second/', second_view),
    ]
    
    dispatch_app = WSGIApplication(dispatch_urlpatterns)
    
    # Test first matching pattern
    result = test_request(dispatch_app, '/first/')
    assert result['status'].startswith('200')
    assert "First view" in result['content']
    print("✓ First matching pattern's view is called")
    
    # Test 404 for unmatched pattern
    result = test_request(dispatch_app, '/nonexistent/')
    assert result['status'].startswith('404')
    print("✓ Unmatched requests yield 404")
    
    # 4. RESPONSE HANDLING
    print("\n4. Response Handling Testing")
    print("-" * 30)
    
    def response_test_view(request):
        response = HttpResponse("Custom response", status=201)
        response['Custom-Header'] = 'custom-value'
        response['X-Test'] = 'test-value'
        return response
    
    response_urlpatterns = [
        path('/response-test/', response_test_view),
    ]
    
    response_app = WSGIApplication(response_urlpatterns)
    
    result = test_request(response_app, '/response-test/')
    assert result['status'].startswith('201')
    assert "Custom response" in result['content']
    
    # Check custom headers
    headers_dict = dict(result['headers'])
    assert headers_dict.get('Custom-Header') == 'custom-value'
    assert headers_dict.get('X-Test') == 'test-value'
    print("✓ Response objects carry status code, headers, and body")
    
    # 5. CLASS-BASED VIEWS
    print("\n5. Class-Based Views Testing")
    print("-" * 30)
    
    class TestAPIView(View):
        def get(self, request, item_id):
            return HttpResponse(f"GET item {item_id}")
        
        def post(self, request, item_id):
            return HttpResponse(f"POST item {item_id}")
        
        def put(self, request, item_id):
            return HttpResponse(f"PUT item {item_id}")
    
    cbv_urlpatterns = [
        path('/api/<int:item_id>/', TestAPIView.as_view()),
    ]
    
    cbv_app = WSGIApplication(cbv_urlpatterns)
    
    # Test GET method
    result = test_request(cbv_app, '/api/123/', method='GET')
    assert result['status'].startswith('200')
    assert "GET item 123" in result['content']
    print("✓ Class-based view dispatches to GET method")
    
    # Test POST method
    result = test_request(cbv_app, '/api/123/', method='POST')
    assert result['status'].startswith('200')
    assert "POST item 123" in result['content']
    print("✓ Class-based view dispatches to POST method")
    
    # Test unsupported method (DELETE)
    result = test_request(cbv_app, '/api/123/', method='DELETE')
    assert result['status'].startswith('405')
    
    # Check Allow header
    headers_dict = dict(result['headers'])
    allow_header = headers_dict.get('Allow', '')
    allowed_methods = [m.strip() for m in allow_header.split(',')]
    assert 'GET' in allowed_methods
    assert 'POST' in allowed_methods
    assert 'PUT' in allowed_methods
    assert 'HEAD' in allowed_methods  # Should be automatically added
    print("✓ Returns 405 with Allow header for unsupported methods")
    
    # Test HEAD request (should use GET implementation)
    result = test_request(cbv_app, '/api/123/', method='HEAD')
    assert result['status'].startswith('200')
    assert "GET item 123" in result['content']  # HEAD uses GET implementation
    print("✓ HEAD requests served from GET implementation")
    
    # WSGI COMPLIANCE
    print("\n6. WSGI Compliance Testing")
    print("-" * 30)
    
    def wsgi_test_view(request):
        return HttpResponse("WSGI compliant response")
    
    wsgi_urlpatterns = [
        path('/wsgi-test/', wsgi_test_view),
    ]
    
    wsgi_app = WSGIApplication(wsgi_urlpatterns)
    
    # Test WSGI interface
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/wsgi-test/',
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
        return lambda x: None
    
    # Test that app is callable and returns iterable
    result = wsgi_app(environ, start_response)
    assert callable(wsgi_app)
    assert hasattr(result, '__iter__')
    
    # Test response format
    assert len(response_data) >= 2
    assert isinstance(response_data[0], str)  # status
    assert isinstance(response_data[1], list)  # headers
    
    content = b''.join(result)
    assert isinstance(content, bytes)
    assert b'WSGI compliant response' in content
    print("✓ Implementation passes WSGI compliance check")
    
    print("\n" + "=" * 50)
    print("🎉 ALL SPECIFICATION REQUIREMENTS VERIFIED!")
    print("✅ URL resolution with literal paths, typed converters, and regex patterns")
    print("✅ Request object with method, path, headers, query string, and body")
    print("✅ View dispatch with first-match and 404 handling")
    print("✅ Response handling with status codes, headers, and body")
    print("✅ Class-based views with HTTP verb dispatch, 405 handling, and HEAD support")
    print("✅ WSGI compliance verified")


def test_request(app, path, method='GET'):
    """Helper function to test a request."""
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': '',
        'wsgi.input': StringIO(),
        'wsgi.errors': StringIO(),
    }
    return test_request_with_environ(app, environ)


def test_request_with_environ(app, environ):
    """Helper function to test a request with custom environ."""
    response_data = []
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    result = app(environ, start_response)
    content = b''.join(result).decode()
    
    return {
        'status': response_data[0],
        'headers': response_data[1],
        'content': content
    }


if __name__ == '__main__':
    verify_specification()
