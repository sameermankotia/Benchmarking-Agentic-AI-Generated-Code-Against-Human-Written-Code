#!/usr/bin/env python3
"""
Example Django-style WSGI application demonstrating all features.
"""

from djangoframework import (
    path, re_path, HttpResponse, JsonResponse, View, get_wsgi_application
)


# Function-based views
def home(request):
    """Home page view."""
    return HttpResponse("""
    <html>
    <head><title>Django Framework Example</title></head>
    <body>
        <h1>Welcome to Django Framework!</h1>
        <p>This is a Django-style WSGI framework demonstration.</p>
        <ul>
            <li><a href="/user/123/">User Detail (ID: 123)</a></li>
            <li><a href="/post/my-awesome-post/">Post Detail (Slug)</a></li>
            <li><a href="/api/users/">JSON API Example</a></li>
            <li><a href="/class-view/">Class-Based View</a></li>
            <li><a href="/archive/2023/">Year Archive (Regex)</a></li>
        </ul>
    </body>
    </html>
    """)


def user_detail(request, user_id):
    """User detail view with integer parameter."""
    return HttpResponse(f"""
    <html>
    <head><title>User {user_id}</title></head>
    <body>
        <h1>User Profile</h1>
        <p>User ID: {user_id} (Type: {type(user_id).__name__})</p>
        <p>Request Method: {request.method}</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)


def post_detail(request, slug):
    """Post detail view with slug parameter."""
    return HttpResponse(f"""
    <html>
    <head><title>Post: {slug}</title></head>
    <body>
        <h1>Post Detail</h1>
        <p>Post Slug: {slug}</p>
        <p>Request Method: {request.method}</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)


def api_users(request):
    """JSON API endpoint."""
    users = [
        {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
        {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
        {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'},
    ]
    
    return JsonResponse({
        'users': users,
        'count': len(users),
        'method': request.method,
        'path': request.path
    })


def year_archive(request, year):
    """Year archive view using regex pattern."""
    return HttpResponse(f"""
    <html>
    <head><title>Archive {year}</title></head>
    <body>
        <h1>Archive for {year}</h1>
        <p>Year: {year} (matched with regex pattern)</p>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    """)


# Class-based view
class ExampleView(View):
    """Example class-based view supporting multiple HTTP methods."""
    
    def get(self, request, *args, **kwargs):
        return HttpResponse("""
        <html>
        <head><title>Class-Based View</title></head>
        <body>
            <h1>Class-Based View (GET)</h1>
            <p>This is a GET request to a class-based view.</p>
            <form method="post">
                <p>Try a POST request:</p>
                <input type="text" name="message" placeholder="Enter a message">
                <button type="submit">Submit POST</button>
            </form>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """)
    
    def post(self, request, *args, **kwargs):
        return HttpResponse("""
        <html>
        <head><title>Class-Based View</title></head>
        <body>
            <h1>Class-Based View (POST)</h1>
            <p>This is a POST request to a class-based view.</p>
            <p>Form data received successfully!</p>
            <p><a href="/class-view/">Try GET request</a></p>
            <p><a href="/">Back to Home</a></p>
        </body>
        </html>
        """)
    
    def put(self, request, *args, **kwargs):
        return JsonResponse({
            'message': 'PUT request received',
            'method': request.method
        })


# URL patterns
urlpatterns = [
    path('', home, name='home'),
    path('user/<int:user_id>/', user_detail, name='user_detail'),
    path('post/<slug:slug>/', post_detail, name='post_detail'),
    path('api/users/', api_users, name='api_users'),
    path('class-view/', ExampleView.as_view(), name='class_view'),
    re_path(r'^archive/(?P<year>[0-9]{4})/$', year_archive, name='year_archive'),
]

# Create WSGI application
application = get_wsgi_application(urlpatterns)


if __name__ == '__main__':
    # Run development server
    from wsgiref.simple_server import make_server
    
    print("Starting Django Framework Example Server...")
    print("Visit http://localhost:8000/ to see the example application")
    print("Press Ctrl+C to stop the server")
    
    server = make_server('localhost', 8000, application)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
