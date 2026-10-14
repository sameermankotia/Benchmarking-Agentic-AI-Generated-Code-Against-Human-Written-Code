# FlaskPair

FlaskPair is a lightweight WSGI-compatible micro web framework for Python 3.11. It provides essential features for building web applications, including routing, request and response objects, template rendering, application context management, and modular applications.

## Features

1. URL routing with variable segments and HTTP method filtering.
2. Request object encapsulating method, path, headers, query string, and body.
3. Response object with status code, headers, and body.
4. Jinja2 template rendering integrated with the application context.
5. Application context management using thread-local storage (`current_app` and `g`).
6. Blueprint-based modular applications with URL prefix inheritance.

## Installation

```bash
pip install .
```

## Usage

```python
from flask_pair import FlaskPair

app = FlaskPair()

@app.route("/hello/<name>", methods=["GET"])
def hello(name):
    return {
        "status": "200 OK",
        "headers": [("Content-Type", "text/plain")],
        "body": f"Hello, {name}!"
    }

if __name__ == "__main__":
    app.run()
```

## Development Server

Run the development server:

```bash
python -m flask_pair
```

## License

MIT License
