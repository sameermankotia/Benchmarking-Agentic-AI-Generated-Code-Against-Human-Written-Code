#!/usr/bin/env python3
"""
Integration test demonstrating all Django Framework features working together.
"""

import uuid
import json
from djangoframework import (
    path, re_path, HttpResponse, JsonResponse, View, 
    get_wsgi_application
)


def create_test_environ(method='GET', path='/', query='', body=b''):
    """Create a test WSGI environ."""
    from io import BytesIO
    return {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query,
        'CONTENT_LENGTH': str(len(body)),
        'wsgi.input': BytesIO(body),
        'wsgi.errors': BytesIO(),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'SERVER_NAME': 'testserver',
        'SERVER_PORT': '80',
    }


# Test views
def home(request):
    return HttpResponse("Django Framework Integration Test")


def user_profile(request, user_id):
    return JsonResponse({
        'user_id': user_id,
        'type': type(user_id).__name__,
        'method': request.method
    })


def article_detail(request, slug):
    return HttpResponse(f"Article: {slug}")


def file_download(request, filepath):
    return HttpResponse(f"Downloading: {filepath}")


def item_view(request, item_id):
    return JsonResponse({
        'item_id': str(item_id),
        'uuid_type': type(item_id).__name__
    })


def year_posts(request, year):
    return HttpResponse(f"Posts from {year}")


class APIView(View):
    """Test class-based view with multiple methods."""
    
    def get(self, request):
        return JsonResponse({'method': 'GET', 'message': 'API GET endpoint'})
    
    def post(self, request):
        return JsonResponse({'method': 'POST', 'message': 'API POST endpoint'})
    
    def put(self, request):
        return JsonResponse({'method': 'PUT', 'message': 'API PUT endpoint'})
    
    def delete(self, request):
        return JsonResponse({'method': 'DELETE', 'message': 'API DELETE endpoint'})


class HeadTestView(View):
    """Test HEAD request handling."""
    
    def get(self, request):
        response = HttpResponse("This content should be empty for HEAD requests")
        response['X-Custom-Header'] = 'custom-value'
        response['Content-Length'] = str(len(response.content))
        return response


# URL patterns covering all features
urlpatterns = [
    # Basic path
    path('', home),
    
    # Type converters
    path('user/<int:user_id>/', user_profile),
    path('article/<slug:slug>/', article_detail),
    path('download/<path:filepath>/', file_download),
    path('item/<uuid:item_id>/', item_view),
    
    # Class-based views
    path('api/', APIView.as_view()),
    path('head-test/', HeadTestView.as_view()),
    
    # Regular expression
    re_path(r'^posts/(?P<year>[0-9]{4})/$', year_posts),
]


def run_integration_tests():
    """Run comprehensive integration tests."""
    print("Django Framework Integration Tests")
    print("=" * 50)
    
    app = get_wsgi_application(urlpatterns)
    
    test_cases = [
        # (description, method, path, expected_status, expected_content_check)
        ("Home page", "GET", "/", "200", lambda c: b"Integration Test" in c),
        ("Integer converter", "GET", "/user/42/", "200", lambda c: b'"user_id": 42' in c and b'"type": "int"' in c),
        ("Slug converter", "GET", "/article/my-test-article/", "200", lambda c: b"Article: my-test-article" in c),
        ("Path converter", "GET", "/download/path/to/file.txt/", "200", lambda c: b"Downloading: path/to/file.txt" in c),
        ("UUID converter", "GET", f"/item/{uuid.uuid4()}/", "200", lambda c: b'"uuid_type": "UUID"' in c),
        ("Regex pattern", "GET", "/posts/2023/", "200", lambda c: b"Posts from 2023" in c),
        ("Class-based GET", "GET", "/api/", "200", lambda c: b'"method": "GET"' in c),
        ("Class-based POST", "POST", "/api/", "200", lambda c: b'"method": "POST"' in c),
        ("Class-based PUT", "PUT", "/api/", "200", lambda c: b'"method": "PUT"' in c),
        ("Class-based DELETE", "DELETE", "/api/", "200", lambda c: b'"method": "DELETE"' in c),
        ("HEAD request", "HEAD", "/head-test/", "200", lambda c: len(c) == 0),  # HEAD should have empty body
        ("404 Not Found", "GET", "/nonexistent/", "404", lambda c: True),
        ("405 Method Not Allowed", "PATCH", "/api/", "405", lambda c: True),
    ]
    
    passed = 0
    failed = 0
    
    for description, method, path, expected_status, content_check in test_cases:
        try:
            environ = create_test_environ(method, path)
            
            responses = []
            def start_response(status, headers):
                responses.append((status, headers))
                return lambda s: None
            
            result = app(environ, start_response)
            content = b''.join(result)
            
            status, headers = responses[0]
            
            # Check status
            if not status.startswith(expected_status):
                raise AssertionError(f"Expected {expected_status}, got {status}")
            
            # Check content
            if not content_check(content):
                raise AssertionError(f"Content check failed for: {content}")
            
            # Additional checks for specific cases
            if method == "HEAD":
                # HEAD should have same headers as GET but empty body
                if len(content) != 0:
                    raise AssertionError("HEAD response should have empty body")
                
                # Check for custom header
                custom_header_found = False
                for name, value in headers:
                    if name == 'X-Custom-Header' and value == 'custom-value':
                        custom_header_found = True
                        break
                if not custom_header_found:
                    raise AssertionError("HEAD response should include custom headers")
            
            if expected_status == "405":
                # Check for Allow header
                allow_header_found = False
                for name, value in headers:
                    if name.lower() == 'allow':
                        allow_header_found = True
                        break
                if not allow_header_found:
                    raise AssertionError("405 response should include Allow header")
            
            print(f"✓ {description}")
            passed += 1
            
        except Exception as e:
            print(f"✗ {description}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("Django Framework is fully functional and ready for use!")
        return True
    else:
        print("❌ Some integration tests failed.")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)
