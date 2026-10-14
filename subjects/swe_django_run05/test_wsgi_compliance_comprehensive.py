#!/usr/bin/env python3
"""Comprehensive WSGI compliance test."""

import io
import uuid
from djangoframework import (
    HttpRequest, HttpResponse, JsonResponse, path, re_path, 
    get_wsgi_application, View
)


def test_wsgi_interface():
    """Test that the application conforms to WSGI interface."""
    
    def simple_view(request):
        return HttpResponse("Hello WSGI!")
    
    urlpatterns = [path('/', simple_view)]
    app = get_wsgi_application(urlpatterns)
    
    # Test that app is callable
    assert callable(app)
    
    # Test WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': 'text/plain',
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
    
    # Test start_response
    response_data = {}
    def start_response(status, response_headers, exc_info=None):
        response_data['status'] = status
        response_data['headers'] = response_headers
        response_data['exc_info'] = exc_info
        return lambda x: None  # write function
    
    # Call application
    result = app(environ, start_response)
    
    # Test return value is iterable
    assert hasattr(result, '__iter__')
    
    # Test response
    response_body = b''.join(result)
    assert response_body == b'Hello WSGI!'
    assert response_data['status'] == '200 OK'
    assert isinstance(response_data['headers'], list)
    
    print("✓ WSGI interface compliance test passed")


def test_all_http_methods():
    """Test all HTTP methods with class-based views."""
    
    class AllMethodsView(View):
        def get(self, request):
            return HttpResponse("GET response")
        
        def post(self, request):
            return HttpResponse("POST response")
        
        def put(self, request):
            return HttpResponse("PUT response")
        
        def patch(self, request):
            return HttpResponse("PATCH response")
        
        def delete(self, request):
            return HttpResponse("DELETE response")
        
        def options(self, request):
            return HttpResponse("OPTIONS response")
    
    urlpatterns = [path('/test/', AllMethodsView.as_view())]
    app = get_wsgi_application(urlpatterns)
    
    methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD']
    
    for method in methods:
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': '/test/',
            'QUERY_STRING': '',
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': '',
            'wsgi.input': io.BytesIO(b''),
        }
        
        response_data = {}
        def start_response(status, headers):
            response_data['status'] = status
            response_data['headers'] = headers
        
        response = app(environ, start_response)
        response_body = b''.join(response)
        
        if method == 'HEAD':
            # HEAD should return empty body but same headers as GET
            assert response_body == b''
            assert response_data['status'] == '200 OK'
        else:
            assert response_data['status'] == '200 OK'
            assert f'{method} response'.encode() in response_body
    
    print("✓ All HTTP methods test passed")


def test_all_converters():
    """Test all URL parameter converters."""
    
    def str_view(request, name):
        return HttpResponse(f"String: {name} ({type(name).__name__})")
    
    def int_view(request, number):
        return HttpResponse(f"Integer: {number} ({type(number).__name__})")
    
    def slug_view(request, slug):
        return HttpResponse(f"Slug: {slug} ({type(slug).__name__})")
    
    def uuid_view(request, token):
        return HttpResponse(f"UUID: {token} ({type(token).__name__})")
    
    def path_view(request, filepath):
        return HttpResponse(f"Path: {filepath} ({type(filepath).__name__})")
    
    urlpatterns = [
        path('/str/<str:name>/', str_view),
        path('/int/<int:number>/', int_view),
        path('/slug/<slug:slug>/', slug_view),
        path('/uuid/<uuid:token>/', uuid_view),
        path('/path/<path:filepath>/', path_view),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    # Test cases
    test_cases = [
        ('/str/hello/', b'String: hello (str)'),
        ('/int/42/', b'Integer: 42 (int)'),
        ('/slug/my-article/', b'Slug: my-article (str)'),
        ('/uuid/550e8400-e29b-41d4-a716-446655440000/', b'UUID: 550e8400-e29b-41d4-a716-446655440000 (UUID)'),
        ('/path/documents/file.txt/', b'Path: documents/file.txt (str)'),
    ]
    
    for path_info, expected in test_cases:
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path_info,
            'QUERY_STRING': '',
            'CONTENT_TYPE': '',
            'CONTENT_LENGTH': '',
            'wsgi.input': io.BytesIO(b''),
        }
        
        response_data = {}
        def start_response(status, headers):
            response_data['status'] = status
            response_data['headers'] = headers
        
        response = app(environ, start_response)
        response_body = b''.join(response)
        
        assert response_data['status'] == '200 OK'
        assert expected in response_body
    
    print("✓ All converters test passed")


def test_error_handling():
    """Test error handling (404, 405, 500)."""
    
    class LimitedView(View):
        def get(self, request):
            return HttpResponse("GET only")
    
    def error_view(request):
        raise ValueError("Test error")
    
    urlpatterns = [
        path('/limited/', LimitedView.as_view()),
        path('/error/', error_view),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    # Test 404
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/nonexistent/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': io.BytesIO(b''),
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '404 Not Found'
    
    # Test 405
    environ['PATH_INFO'] = '/limited/'
    environ['REQUEST_METHOD'] = 'POST'
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '405 Method Not Allowed'
    
    # Check Allow header
    allow_header = None
    for name, value in response_data['headers']:
        if name == 'Allow':
            allow_header = value
            break
    assert allow_header is not None
    assert 'GET' in allow_header
    
    # Test 500
    environ['PATH_INFO'] = '/error/'
    environ['REQUEST_METHOD'] = 'GET'
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '500 Internal Server Error'
    
    print("✓ Error handling test passed")


def test_json_response():
    """Test JSON response functionality."""
    
    def json_view(request):
        return JsonResponse({
            'message': 'Hello JSON',
            'method': request.method,
            'path': request.path
        })
    
    urlpatterns = [path('/json/', json_view)]
    app = get_wsgi_application(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/json/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': io.BytesIO(b''),
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    
    # Check content type
    content_type = None
    for name, value in response_data['headers']:
        if name == 'Content-Type':
            content_type = value
            break
    assert content_type == 'application/json'
    
    # Check JSON content
    assert b'"message": "Hello JSON"' in response_body
    assert b'"method": "GET"' in response_body
    assert b'"path": "/json/"' in response_body
    
    print("✓ JSON response test passed")


if __name__ == '__main__':
    test_wsgi_interface()
    test_all_http_methods()
    test_all_converters()
    test_error_handling()
    test_json_response()
    print("\n🎉 All comprehensive WSGI compliance tests passed!")
    print("The Django-like framework is fully WSGI compliant!")
