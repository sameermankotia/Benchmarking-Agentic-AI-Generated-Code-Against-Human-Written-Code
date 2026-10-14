#!/usr/bin/env python3
"""
WSGI compliance test using wsgiref.validate.
"""

import sys
import os
from io import BytesIO

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wsgiref.validate import validator
from djangoframework import WSGIApplication, HttpResponse, path


def simple_view(request):
    return HttpResponse("WSGI Compliance Test")


urlpatterns = [
    path('', simple_view),
    path('test/', simple_view),
]

# Create application and wrap with validator
application = WSGIApplication(urlpatterns)
validated_app = validator(application)

# Test WSGI compliance
def test_wsgi_compliance():
    """Test WSGI compliance using wsgiref validator."""
    
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/test/',
        'SCRIPT_NAME': '',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'HTTP_HOST': 'localhost:8000',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': BytesIO(b''),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    responses = []
    def start_response(status, headers, exc_info=None):
        responses.append((status, headers))
    
    try:
        # This will raise an exception if the app is not WSGI compliant
        result = validated_app(environ, start_response)
        content = b''.join(result)
        
        print("✅ WSGI compliance test passed!")
        print(f"Status: {responses[0][0]}")
        print(f"Content: {content}")
        return True
        
    except Exception as e:
        print(f"❌ WSGI compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Running WSGI compliance test...")
    success = test_wsgi_compliance()
    sys.exit(0 if success else 1)
