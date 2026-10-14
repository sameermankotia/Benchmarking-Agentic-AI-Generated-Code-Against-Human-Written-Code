#!/usr/bin/env python3
"""Debug 500 error handling."""

import io
from djangoframework import HttpResponse, path, get_wsgi_application

def error_view(request):
    raise ValueError("Test error")

urlpatterns = [
    path('/error/', error_view),
]

app = get_wsgi_application(urlpatterns)

environ = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/error/',
    'QUERY_STRING': '',
    'CONTENT_TYPE': '',
    'CONTENT_LENGTH': '',
    'wsgi.input': io.BytesIO(b''),
}

response_data = {}
def start_response(status, headers):
    print(f"Status: {status}")
    print(f"Headers: {headers}")
    response_data['status'] = status
    response_data['headers'] = headers

response = app(environ, start_response)
response_body = b''.join(response)
print(f"Response body: {response_body}")
print(f"Response data: {response_data}")
