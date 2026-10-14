#!/usr/bin/env python3
"""
WSGI compliance test for FlaskFramework.
"""

import sys
import os
from io import StringIO

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flaskframework import Flask


def test_wsgi_compliance():
    """Test WSGI compliance according to PEP 3333."""
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return 'Hello WSGI World!'
    
    @app.route('/json')
    def json_response():
        return {'message': 'Hello JSON'}
    
    @app.route('/status')
    def custom_status():
        return 'Created', 201
    
    @app.route('/headers')
    def custom_headers():
        return 'Custom Headers', 200, {'X-Custom': 'Test'}
    
    # Test cases
    test_cases = [
        {
            'name': 'Basic GET request',
            'environ': {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/',
                'QUERY_STRING': '',
                'CONTENT_TYPE': '',
                'CONTENT_LENGTH': '0',
                'wsgi.input': StringIO('')
            },
            'expected_status': '200 OK',
            'expected_body': b'Hello WSGI World!'
        },
        {
            'name': 'JSON response',
            'environ': {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/json',
                'QUERY_STRING': '',
                'CONTENT_TYPE': '',
                'CONTENT_LENGTH': '0',
                'wsgi.input': StringIO('')
            },
            'expected_status': '200 OK',
            'expected_body_contains': b'message'
        },
        {
            'name': 'Custom status code',
            'environ': {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/status',
                'QUERY_STRING': '',
                'CONTENT_TYPE': '',
                'CONTENT_LENGTH': '0',
                'wsgi.input': StringIO('')
            },
            'expected_status': '201 Created',
            'expected_body': b'Created'
        },
        {
            'name': 'Custom headers',
            'environ': {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/headers',
                'QUERY_STRING': '',
                'CONTENT_TYPE': '',
                'CONTENT_LENGTH': '0',
                'wsgi.input': StringIO('')
            },
            'expected_status': '200 OK',
            'expected_body': b'Custom Headers',
            'expected_headers': {'X-Custom': 'Test'}
        },
        {
            'name': '404 Not Found',
            'environ': {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/nonexistent',
                'QUERY_STRING': '',
                'CONTENT_TYPE': '',
                'CONTENT_LENGTH': '0',
                'wsgi.input': StringIO('')
            },
            'expected_status': '404 Not Found'
        }
    ]
    
    print("Running WSGI compliance tests...\n")
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        
        # Capture response data
        response_data = {}
        def start_response(status, headers):
            response_data['status'] = status
            response_data['headers'] = dict(headers)
        
        # Call WSGI app
        result = app(test_case['environ'], start_response)
        response_body = b''.join(result)
        
        # Check status
        assert response_data['status'] == test_case['expected_status'], \
            f"Expected status {test_case['expected_status']}, got {response_data['status']}"
        
        # Check body
        if 'expected_body' in test_case:
            assert response_body == test_case['expected_body'], \
                f"Expected body {test_case['expected_body']}, got {response_body}"
        
        if 'expected_body_contains' in test_case:
            assert test_case['expected_body_contains'] in response_body, \
                f"Expected body to contain {test_case['expected_body_contains']}, got {response_body}"
        
        # Check headers
        if 'expected_headers' in test_case:
            for header_name, header_value in test_case['expected_headers'].items():
                assert header_name in response_data['headers'], \
                    f"Expected header {header_name} not found"
                assert response_data['headers'][header_name] == header_value, \
                    f"Expected header {header_name}={header_value}, got {response_data['headers'][header_name]}"
        
        # Check required WSGI headers
        assert 'Content-Length' in response_data['headers'], "Content-Length header required"
        assert response_data['headers']['Content-Length'] == str(len(response_body)), \
            "Content-Length should match body length"
        
        print(f"  ✓ Status: {response_data['status']}")
        print(f"  ✓ Body length: {len(response_body)} bytes")
        print(f"  ✓ Headers: {len(response_data['headers'])} headers")
        print()
    
    print("🎉 All WSGI compliance tests passed!")


if __name__ == '__main__':
    test_wsgi_compliance()
