#!/usr/bin/env python3
"""Example Django-like framework application."""

import uuid
from djangoframework import (
    HttpRequest, HttpResponse, JsonResponse, path, re_path,
    get_wsgi_application, View
)


# Function-based views
def home(request):
    """Home page view."""
    return HttpResponse("""
    <h1>Welcome to Django Framework!</h1>
    <p>This is a Django-like WSGI framework demonstration.</p>
    <ul>
        <li><a href="/hello/world/">Hello World</a></li>
        <li><a href="/user/123/">User Profile</a></li>
        <li><a href="/article/my-first-post/">Article View</a></li>
        <li><a href="/api/item/456/">API Example</a></li>
        <li><a href="/files/documents/report.pdf/">File Path Example</a></li>
    </ul>
    """)


def hello_name(request, name):
    """Greet a specific name."""
    return HttpResponse(f"<h1>Hello, {name}!</h1><p>Nice to meet you.</p>")


def user_profile(request, user_id):
    """Display user profile."""
    return HttpResponse(f"""
    <h1>User Profile</h1>
    <p>User ID: {user_id}</p>
    <p>Method: {request.method}</p>
    <p>Path: {request.path}</p>
    """)


def file_handler(request, filepath):
    """Handle file paths."""
    return HttpResponse(f"""
    <h1>File Handler</h1>
    <p>File path: {filepath}</p>
    <p>This would serve the file in a real application.</p>
    """)


def archive_year(request, year):
    """Archive view for specific year."""
    return HttpResponse(f"""
    <h1>Archive for {year}</h1>
    <p>This would show posts from {year}.</p>
    """)


# Class-based views
class ArticleView(View):
    """Article view with multiple HTTP methods."""
    
    def get(self, request, slug):
        return HttpResponse(f"""
        <h1>Article: {slug}</h1>
        <p>This is the article content for '{slug}'.</p>
        <p>Method: GET</p>
        <form method="post">
            <button type="submit">Update Article</button>
        </form>
        """)
    
    def post(self, request, slug):
        return HttpResponse(f"""
        <h1>Article Updated: {slug}</h1>
        <p>The article '{slug}' has been updated!</p>
        <p>Method: POST</p>
        <a href="/article/{slug}/">View Article</a>
        """)


class APIView(View):
    """RESTful API view."""
    
    def get(self, request, item_id):
        return JsonResponse({
            'id': item_id,
            'method': 'GET',
            'message': f'Retrieved item {item_id}',
            'path': request.path
        })
    
    def post(self, request, item_id):
        return JsonResponse({
            'id': item_id,
            'method': 'POST',
            'message': f'Created/Updated item {item_id}',
            'path': request.path
        })
    
    def delete(self, request, item_id):
        return JsonResponse({
            'id': item_id,
            'method': 'DELETE',
            'message': f'Deleted item {item_id}',
            'path': request.path
        })


class TokenView(View):
    """UUID token handling."""
    
    def get(self, request, token):
        return JsonResponse({
            'token': str(token),
            'type': type(token).__name__,
            'valid': True,
            'message': 'Token is valid'
        })


# URL patterns
urlpatterns = [
    # Basic paths
    path('/', home),
    path('hello/<str:name>/', hello_name),
    
    # Typed parameters
    path('user/<int:user_id>/', user_profile),
    path('article/<slug:slug>/', ArticleView.as_view()),
    path('token/<uuid:token>/', TokenView.as_view()),
    path('files/<path:filepath>/', file_handler),
    
    # API endpoints
    path('api/item/<int:item_id>/', APIView.as_view()),
    
    # Regex patterns
    re_path(r'^/archive/(?P<year>\d{4})/$', archive_year),
]

# Create WSGI application
application = get_wsgi_application(urlpatterns)


if __name__ == '__main__':
    # Development server (not for production use)
    from wsgiref.simple_server import make_server
    
    print("Starting Django Framework development server...")
    print("Server running on http://localhost:8000/")
    print("Press Ctrl+C to stop the server")
    
    try:
        server = make_server('localhost', 8000, application)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
