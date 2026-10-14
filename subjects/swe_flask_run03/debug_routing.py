from flaskframework import Flask
from io import StringIO
import sys

app = Flask(__name__)

@app.route('/user/<name>')
def user_profile(name):
    return f'User: {name}'

@app.route('/user/<int:user_id>')
def user_by_id(user_id):
    return f'User ID: {user_id}'

# Test routing
environ = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/user/123',
    'QUERY_STRING': '',
    'CONTENT_TYPE': '',
    'CONTENT_LENGTH': '0',
    'wsgi.input': StringIO(),
    'wsgi.version': (1, 0),
    'wsgi.url_scheme': 'http',
    'wsgi.errors': sys.stderr,
    'wsgi.multithread': False,
    'wsgi.multiprocess': True,
    'wsgi.run_once': False
}

def start_response(status, headers):
    print(f"Status: {status}")
    print(f"Headers: {headers}")

result = app(environ, start_response)
response_body = b''.join(result)
print(f"Response: {response_body}")

# Debug the router
print("\nRouter rules:")
for i, rule in enumerate(app.router.rules):
    print(f"Rule {i}: {rule.pattern} -> {rule.endpoint}")
    print(f"  Regex: {rule.regex.pattern}")
    print(f"  Variables: {rule.variables}")
    match_result = rule.match('/user/123', 'GET')
    print(f"  Match result: {match_result}")
