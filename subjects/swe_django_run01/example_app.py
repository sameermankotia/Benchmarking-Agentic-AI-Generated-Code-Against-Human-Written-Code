#!/usr/bin/env python3
"""
Example application demonstrating the Django-style framework.
"""

from djangoframework import WSGIApplication, HttpResponse, View, path, re_path


# Function-based views
def home_view(request):
    """Home page view."""
    return HttpResponse("""
    <html>
        <head><title>Django Framework Demo</title></head>
        <body>
            <h1>Welcome to Django Framework</h1>
            <p>This is a WSGI-compatible URL routing and view dispatching framework.</p>
            <ul>
                <li><a href="/hello/world/">Hello World</a></li>
                <li><a href="/user/123/">User 123</a></li>
                <li><a href="/article/my-article/">Article View</a></li>
                <li><a href="/files/docs/readme.txt/">File View</a></li>
                <li><a href="/api/items/456/">API Item (Class-based)</a></li>
                <li><a href="/archive/2023/">Archive 2023</a></li>
            </ul>
        </body>
    </html>
    """)


def hello_view(request, name):
    """Hello view with name parameter."""
    return HttpResponse(f"""
    <html>
        <head><title>Hello {name}</title></head>
        <body>
            <h1>Hello, {name}!</h1>
            <p>Method: {request.method}</p>
            <p>Path: {request.path}</p>
            <p><a href="/">Back to home</a></p>
        </body>
    </html>
    """)


def user_view(request, user_id):
    """User view with integer ID."""
    return HttpResponse(f"""
    <html>
        <head><title>User {user_id}</title></head>
        <body>
            <h1>User Profile</h1>
            <p>User ID: {user_id} (type: {type(user_id).__name__})</p>
            <p>Method: {request.method}</p>
            <p><a href="/">Back to home</a></p>
        </body>
    </html>
    """)


def article_view(request, title):
    """Article view with slug title."""
    return HttpResponse(f"""
    <html>
        <head><title>Article: {title}</title></head>
        <body>
            <h1>Article: {title}</h1>
            <p>This is the article page for "{title}"</p>
            <p><a href="/">Back to home</a></p>
        </body>
    </html>
    """)


def file_view(request, filepath):
    """File view with path parameter."""
    return HttpResponse(f"""
    <html>
        <head><title>File: {filepath}</title></head>
        <body>
            <h1>File Viewer</h1>
            <p>File path: {filepath}</p>
            <p>This would serve the file: {filepath}</p>
            <p><a href="/">Back to home</a></p>
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
            <p>This is the archive page for year {year}</p>
            <p><a href="/">Back to home</a></p>
        </body>
    </html>
    """)


# Class-based view
class APIItemView(View):
    """API item view demonstrating class-based views."""
    
    def get(self, request, item_id):
        """Handle GET requests."""
        return HttpResponse(f"""
        <html>
            <head><title>API Item {item_id}</title></head>
            <body>
                <h1>API Item {item_id}</h1>
                <p>GET request received</p>
                <p>Item ID: {item_id} (type: {type(item_id).__name__})</p>
                <p>Try POST, PUT, or DELETE to see different responses</p>
                <p><a href="/">Back to home</a></p>
            </body>
        </html>
        """)
    
    def post(self, request, item_id):
        """Handle POST requests."""
        return HttpResponse(f"""
        <html>
            <head><title>API Item {item_id} - Created</title></head>
            <body>
                <h1>Item {item_id} Created</h1>
                <p>POST request received</p>
                <p><a href="/api/items/{item_id}/">View item</a></p>
                <p><a href="/">Back to home</a></p>
            </body>
        </html>
        """)
    
    def put(self, request, item_id):
        """Handle PUT requests."""
        return HttpResponse(f"""
        <html>
            <head><title>API Item {item_id} - Updated</title></head>
            <body>
                <h1>Item {item_id} Updated</h1>
                <p>PUT request received</p>
                <p><a href="/api/items/{item_id}/">View item</a></p>
                <p><a href="/">Back to home</a></p>
            </body>
        </html>
        """)
    
    def delete(self, request, item_id):
        """Handle DELETE requests."""
        return HttpResponse(f"""
        <html>
            <head><title>API Item {item_id} - Deleted</title></head>
            <body>
                <h1>Item {item_id} Deleted</h1>
                <p>DELETE request received</p>
                <p><a href="/">Back to home</a></p>
            </body>
        </html>
        """)


# URL patterns
urlpatterns = [
    # Function-based views with path patterns
    path('/', home_view),
    path('/hello/<str:name>/', hello_view),
    path('/user/<int:user_id>/', user_view),
    path('/article/<slug:title>/', article_view),
    path('/files/<path:filepath>/', file_view),
    
    # Class-based view
    path('/api/items/<int:item_id>/', APIItemView.as_view()),
    
    # Regex pattern
    re_path(r'^/archive/(?P<year>[0-9]{4})/$', archive_view),
]

# Create WSGI application
application = WSGIApplication(urlpatterns)


if __name__ == '__main__':
    # Run with Python's built-in WSGI server for development
    from wsgiref.simple_server import make_server
    
    print("Starting Django Framework demo server...")
    print("Visit http://localhost:8000 to see the demo")
    print("Press Ctrl+C to stop the server")
    
    server = make_server('localhost', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
