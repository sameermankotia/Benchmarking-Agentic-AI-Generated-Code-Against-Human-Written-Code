"""Test WSGI compliance and basic functionality."""

import uuid
from djangoframework import (
    HttpRequest, HttpResponse, JsonResponse, path, re_path, 
    get_wsgi_application, View
)


def test_basic_wsgi_compliance():
    """Test basic WSGI compliance."""
    
    def hello_view(request):
        return HttpResponse("Hello, World!")
    
    urlpatterns = [
        path('/', hello_view),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    # Mock WSGI environ
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    # Mock start_response
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    # Call the WSGI app
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'Hello, World!'
    assert ('Content-Type', 'text/html') in response_data['headers']
    print("✓ Basic WSGI compliance test passed")


def test_url_resolution_with_converters():
    """Test URL resolution with different parameter types."""
    
    def string_view(request, name):
        return HttpResponse(f"Hello, {name}!")
    
    def int_view(request, user_id):
        return HttpResponse(f"User ID: {user_id}")
    
    def slug_view(request, article_slug):
        return HttpResponse(f"Article: {article_slug}")
    
    def uuid_view(request, token):
        return HttpResponse(f"Token: {token}")
    
    def path_view(request, filepath):
        return HttpResponse(f"File: {filepath}")
    
    urlpatterns = [
        path('hello/<str:name>/', string_view),
        path('user/<int:user_id>/', int_view),
        path('article/<slug:article_slug>/', slug_view),
        path('token/<uuid:token>/', uuid_view),
        path('files/<path:filepath>/', path_view),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    # Test string parameter
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/hello/john/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'Hello, john!'
    print("✓ String parameter test passed")
    
    # Test integer parameter
    environ['PATH_INFO'] = '/user/123/'
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'User ID: 123'
    print("✓ Integer parameter test passed")
    
    # Test slug parameter
    environ['PATH_INFO'] = '/article/my-awesome-article/'
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'Article: my-awesome-article'
    print("✓ Slug parameter test passed")
    
    # Test UUID parameter
    test_uuid = str(uuid.uuid4())
    environ['PATH_INFO'] = f'/token/{test_uuid}/'
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == f'Token: {test_uuid}'.encode()
    print("✓ UUID parameter test passed")
    
    # Test path parameter
    environ['PATH_INFO'] = '/files/documents/report.pdf/'
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'File: documents/report.pdf'
    print("✓ Path parameter test passed")


def test_404_handling():
    """Test 404 response for unmatched URLs."""
    
    def home_view(request):
        return HttpResponse("Home")
    
    urlpatterns = [
        path('/', home_view),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/nonexistent/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '404 Not Found'
    assert b'Not Found' in response_body
    print("✓ 404 handling test passed")


def test_class_based_views():
    """Test class-based view functionality."""
    
    class TestView(View):
        def get(self, request, item_id):
            return HttpResponse(f"GET item {item_id}")
        
        def post(self, request, item_id):
            return HttpResponse(f"POST item {item_id}")
    
    urlpatterns = [
        path('item/<int:item_id>/', TestView.as_view()),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    # Test GET request
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/item/42/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'GET item 42'
    print("✓ Class-based view GET test passed")
    
    # Test POST request
    environ['REQUEST_METHOD'] = 'POST'
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'POST item 42'
    print("✓ Class-based view POST test passed")


def test_method_not_allowed():
    """Test 405 Method Not Allowed for unsupported HTTP methods."""
    
    class GetOnlyView(View):
        def get(self, request):
            return HttpResponse("GET only")
    
    urlpatterns = [
        path('get-only/', GetOnlyView.as_view()),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/get-only/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '405 Method Not Allowed'
    
    # Check Allow header
    allow_header = None
    for header_name, header_value in response_data['headers']:
        if header_name == 'Allow':
            allow_header = header_value
            break
    
    assert allow_header is not None
    assert 'GET' in allow_header
    assert 'HEAD' in allow_header  # Should include HEAD since GET is available
    print("✓ Method Not Allowed test passed")


def test_head_request_handling():
    """Test HEAD request handling via GET method."""
    
    class TestView(View):
        def get(self, request):
            return HttpResponse("This is the body content")
    
    urlpatterns = [
        path('test/', TestView.as_view()),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'HEAD',
        'PATH_INFO': '/test/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b''  # HEAD should have empty body
    print("✓ HEAD request handling test passed")


def test_regex_patterns():
    """Test regular expression URL patterns."""
    
    def year_view(request, year):
        return HttpResponse(f"Year: {year}")
    
    urlpatterns = [
        re_path(r'^/archive/(?P<year>\d{4})/$', year_view),
    ]
    
    app = get_wsgi_application(urlpatterns)
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/archive/2023/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response_data = {}
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    assert response_data['status'] == '200 OK'
    assert response_body == b'Year: 2023'
    print("✓ Regex pattern test passed")


if __name__ == '__main__':
    test_basic_wsgi_compliance()
    test_url_resolution_with_converters()
    test_404_handling()
    test_class_based_views()
    test_method_not_allowed()
    test_head_request_handling()
    test_regex_patterns()
    print("\n✅ All tests passed! WSGI compliance verified.")
