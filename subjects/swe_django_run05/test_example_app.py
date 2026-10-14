#!/usr/bin/env python3
"""Test the example application."""

from example_app import application

def test_example_app():
    """Test various routes in the example application."""
    
    def mock_start_response(status, headers):
        print(f"Status: {status}")
        return lambda x: None
    
    # Test home page
    environ = {
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'CONTENT_TYPE': '',
        'CONTENT_LENGTH': '',
        'wsgi.input': None,
    }
    
    response = application(environ, mock_start_response)
    response_body = b''.join(response)
    assert b'Welcome to Django Framework!' in response_body
    print("✓ Home page test passed")
    
    # Test hello with name
    environ['PATH_INFO'] = '/hello/world/'
    response = application(environ, mock_start_response)
    response_body = b''.join(response)
    assert b'Hello, world!' in response_body
    print("✓ Hello name test passed")
    
    # Test user profile
    environ['PATH_INFO'] = '/user/123/'
    response = application(environ, mock_start_response)
    response_body = b''.join(response)
    assert b'User ID: 123' in response_body
    print("✓ User profile test passed")
    
    # Test API endpoint
    environ['PATH_INFO'] = '/api/item/456/'
    response = application(environ, mock_start_response)
    response_body = b''.join(response)
    assert b'"id": 456' in response_body
    print("✓ API endpoint test passed")
    
    # Test archive regex
    environ['PATH_INFO'] = '/archive/2023/'
    response = application(environ, mock_start_response)
    response_body = b''.join(response)
    assert b'Archive for 2023' in response_body
    print("✓ Archive regex test passed")
    
    print("\n✅ All example app tests passed!")

if __name__ == '__main__':
    test_example_app()
