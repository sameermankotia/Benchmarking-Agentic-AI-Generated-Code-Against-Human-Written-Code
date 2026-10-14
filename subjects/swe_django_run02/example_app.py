#!/usr/bin/env python3
"""
Example Django Framework application demonstrating all features.
"""

import uuid
from djangoframework import (
    path, re_path, HttpRequest, HttpResponse, View, WSGIApplication
)


# Function-based views
def home(request):
    """Home page view."""
    return HttpResponse("""
    <html>
    <head><title>Django Framework Demo</title></head>
    <body>
        <h1>Welcome to Django Framework!</h1>
        <p>This is a demonstration of the Django-like WSGI framework.</p>
        <ul>
            <li><a href="/hello/world/">Hello World</a></li>
            <li><a href="/article/123/">Article 123</a></li>
            <li><a href="/category/python-tips/">Python Tips Category</a></li>
            <li><a href="/files/docs/readme.txt/">File Path Example</a></li>
            <li><a href="/archive/2023/">Archive 2023</a></li>
            <li><a href="/api/">API View (Class-based)</a></li>
        </ul>
    </body>
    </html>
    """)


def hello_view(request, name):
    """Greet a user by name."""
    return HttpResponse(f"""
    <html>
    <head><title>Hello {name}</title></head>
    <body>
        <h1>Hello, {name}!</h1>
        <p>This demonstrates string parameter conversion.</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """)


def article_view(request, id):
    """Display an article by ID."""
    return HttpResponse(f"""
    <html>
    <head><title>Article {id}</title></head>
    <body>
        <h1>Article #{id}</h1>
        <p>This demonstrates integer parameter conversion.</p>
        <p>The ID parameter is of type: {type(id).__name__}</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """)


def category_view(request, category):
    """Display a category page."""
    return HttpResponse(f"""
    <html>
    <head><title>Category: {category}</title></head>
    <body>
        <h1>Category: {category}</h1>
        <p>This demonstrates slug parameter conversion.</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """)


def file_view(request, filepath):
    """Display file path."""
    return HttpResponse(f"""
    <html>
    <head><title>File: {filepath}</title></head>
    <body>
        <h1>File Path: {filepath}</h1>
        <p>This demonstrates path parameter conversion (includes slashes).</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """)


def archive_view(request, year):
    """Archive view using regex pattern."""
    return HttpResponse(f"""
    <html>
    <head><title>Archive {year}</title></head>
    <body>
        <h1>Archive for {year}</h1>
        <p>This demonstrates regex URL patterns.</p>
        <a href="/">Back to home</a>
    </body>
    </html>
    """)


# Class-based view
class APIView(View):
    """Example API view demonstrating class-based views."""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests."""
        return HttpResponse("""
        <html>
        <head><title>API - GET</title></head>
        <body>
            <h1>API View - GET Method</h1>
            <p>This demonstrates class-based views with GET method.</p>
            <p>Try sending a POST request to see method dispatch in action.</p>
            <form method="post">
                <button type="submit">Send POST Request</button>
            </form>
            <a href="/">Back to home</a>
        </body>
        </html>
        """)
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests."""
        return HttpResponse("""
        <html>
        <head><title>API - POST</title></head>
        <body>
            <h1>API View - POST Method</h1>
            <p>This demonstrates class-based views with POST method.</p>
            <p>The view automatically dispatched to the POST method!</p>
            <a href="/api/">Back to API (GET)</a> | <a href="/">Back to home</a>
        </body>
        </html>
        """)


class GetOnlyView(View):
    """View that only supports GET to demonstrate 405 handling."""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests only."""
        return HttpResponse("""
        <html>
        <head><title>GET Only View</title></head>
        <body>
            <h1>GET Only View</h1>
            <p>This view only supports GET requests.</p>
            <p>Try sending a POST request to see 405 Method Not Allowed response.</p>
            <a href="/">Back to home</a>
        </body>
        </html>
        """)


# URL patterns
urlpatterns = [
    path('', home),
    path('hello/<str:name>/', hello_view),
    path('article/<int:id>/', article_view),
    path('category/<slug:category>/', category_view),
    path('files/<path:filepath>/', file_view),
    re_path(r'^archive/(?P<year>[0-9]{4})/$', archive_view),
    path('api/', APIView.as_view()),
    path('get-only/', GetOnlyView.as_view()),
]


# Create WSGI application
application = WSGIApplication(urlpatterns)


if __name__ == '__main__':
    # Simple development server for testing
    from wsgiref.simple_server import make_server
    
    print("Starting Django Framework development server...")
    print("Visit http://localhost:8000/ to see the demo")
    print("Press Ctrl+C to stop the server")
    
    with make_server('localhost', 8000, application) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
