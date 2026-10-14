#!/usr/bin/env python3
"""Debug WSGI application."""

from djangoframework import HttpResponse, path, get_wsgi_application

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
    print(f"Status: {status}")
    print(f"Headers: {headers}")
    response_data['status'] = status
    response_data['headers'] = headers

# Call the WSGI app
try:
    response = app(environ, start_response)
    response_body = b''.join(response)
    print(f"Response body: {response_body}")
    print(f"Response data: {response_data}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
