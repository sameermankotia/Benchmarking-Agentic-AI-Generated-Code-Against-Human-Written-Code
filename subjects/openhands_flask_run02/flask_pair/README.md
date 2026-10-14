
# FlaskPair

FlaskPair is a lightweight WSGI-compatible micro web framework for Python 3.11. It provides essential features for building web applications, including routing, request/response handling, template rendering, and modular application support.

## Features

1. URL routing with variable segments and HTTP method filtering.
2. Request object encapsulating method, path, headers, query string, and body.
3. Response object with status code, headers, and body.
4. Jinja2 template rendering integrated with the application context.
5. Application context management using thread-local storage (`current_app` and `g`).
6. Blueprint-based modular applications with URL prefix inheritance.

## Installation

```bash
pip install flask_pair
```

## Usage

```python
from flask_pair import FlaskPair, Response

app = FlaskPair()

@app.route("/", methods=["GET"])
def home(request):
    return Response("Hello, FlaskPair!")

if __name__ == "__main__":
    app.run()
```

## License

This project is licensed under the MIT License.