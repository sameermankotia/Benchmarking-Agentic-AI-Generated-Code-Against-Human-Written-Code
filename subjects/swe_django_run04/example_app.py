#!/usr/bin/env python3
"""
Example application demonstrating the Django-style WSGI framework.
"""

from djangoframework import WSGIApplication, HttpResponse, View, path, re_path


# Function-based views
def home(request):
    """Home page view."""
    return HttpResponse("""
    <h1>Welcome to Django Framework</h1>
    <p>This is a WSGI-compatible URL routing and view dispatching framework.</p>
    <ul>
        <li><a href="/hello/World/">Hello World</a></li>
        <li><a href="/user/123/">User Profile</a></li>
        <li><a href="/article/456/">Article Detail</a></li>
        <li><a href="/files/docs/readme.txt/">File View</a></li>
        <li><a href="/archive/2023/">Archive</a></li>
    </ul>
    """)


def hello_view(request, name):
    """Greet a user by name."""
    return HttpResponse(f"<h1>Hello, {name}!</h1><p>Nice to meet you.</p>")


def user_profile(request, user_id):
    """Display user profile."""
    return HttpResponse(f"""
    <h1>User Profile</h1>
    <p>User ID: {user_id} (type: {type(user_id).__name__})</p>
    <p>Method: {request.method}</p>
    """)


def file_view(request, filepath):
    """Display file path."""
    return HttpResponse(f"""
    <h1>File View</h1>
    <p>File path: {filepath}</p>
    <p>This demonstrates the path converter that includes slashes.</p>
    """)


def archive_view(request, year):
    """Archive view using regex pattern."""
    return HttpResponse(f"""
    <h1>Archive for {year}</h1>
    <p>This view was matched using a regular expression pattern.</p>
    """)


# Class-based view
class ArticleView(View):
    """Article view with multiple HTTP methods."""
    
    def get(self, request, article_id):
        return HttpResponse(f"""
        <h1>Article {article_id}</h1>
        <p>This is a GET request to view the article.</p>
        <p>Try sending a POST request to update it.</p>
        """)
    
    def post(self, request, article_id):
        return HttpResponse(f"""
        <h1>Article {article_id} Updated</h1>
        <p>This is a POST request to update the article.</p>
        """)


# URL patterns
urlpatterns = [
    path('', home),
    path('hello/<str:name>/', hello_view),
    path('user/<int:user_id>/', user_profile),
    path('article/<int:article_id>/', ArticleView.as_view()),
    path('files/<path:filepath>/', file_view),
    re_path(r'^archive/(?P<year>[0-9]{4})/$', archive_view),
]

# Create WSGI application
application = WSGIApplication(urlpatterns)


if __name__ == '__main__':
    # Run with Python's built-in WSGI server for testing
    from wsgiref.simple_server import make_server
    
    print("Starting Django Framework example server...")
    print("Visit http://localhost:8000 to see the application")
    print("Press Ctrl+C to stop the server")
    
    server = make_server('localhost', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
