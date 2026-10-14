#!/usr/bin/env python3
"""Debug URL converters."""

from djangoframework import HttpResponse, path, get_wsgi_application

def int_view(request, user_id):
    print(f"Received user_id: {user_id}, type: {type(user_id)}")
    return HttpResponse(f"User ID: {user_id}")

urlpatterns = [
    path('user/<int:user_id>/', int_view),
]

app = get_wsgi_application(urlpatterns)

# Mock WSGI environ
environ = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/user/123/',
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
