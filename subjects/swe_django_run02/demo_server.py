#!/usr/bin/env python3
"""
Demo server showing the Django Framework in action.
Run this script to start a development server and test the framework.
"""

from wsgiref.simple_server import make_server
from example_app import application

if __name__ == '__main__':
    print("Django Framework Demo Server")
    print("=" * 40)
    print("Starting server on http://localhost:8000/")
    print("Visit the URL to see the framework in action!")
    print("Press Ctrl+C to stop the server")
    print()
    
    with make_server('localhost', 8000, application) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped. Goodbye!")
