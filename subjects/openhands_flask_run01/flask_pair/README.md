
# Flask Pair

Flask Pair is a WSGI-compatible micro web framework built in Python 3.11. It is designed to provide a lightweight and modular approach to building web applications.

## Features

1. **URL Routing**: Supports variable segments and HTTP method filtering.
2. **Request Object**: Encapsulates method, path, headers, query string, and body.
3. **Response Object**: Includes status code, headers, and body.
4. **Template Rendering**: Integrated Jinja2 template rendering.
5. **Application Context**: Thread-local storage for `current_app` and `g`.
6. **Blueprints**: Modular applications with URL prefix inheritance.

## Installation

To install Flask Pair, clone the repository and install dependencies using Poetry:

```bash
git clone <repository-url>
cd flask_pair
poetry install
```

## Usage

Run the development server:

```bash
poetry run python app.py
```

## License

This project is licensed under the MIT License.