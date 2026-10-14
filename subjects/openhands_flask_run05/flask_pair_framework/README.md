# Flask Pair Framework

This project is a WSGI-compatible micro web framework implemented in Python 3.11. It is designed to meet the following specifications:

1. URL routing with variable segments and HTTP method filtering.
2. Request object encapsulating method, path, headers, query string, and body.
3. Response object with status code, headers, and body.
4. Jinja2 template rendering integrated with the application context.
5. Application context management using thread-local storage so that `current_app` and `g` are accessible within a request.
6. Blueprint-based modular applications with URL prefix inheritance.

## Features

- WSGI compliance.
- Built-in development server.
- Modular and extensible design.

## Installation

To install the framework, clone this repository and use the provided `pyproject.toml` for dependency management.

## Usage

Refer to the documentation and examples provided in this repository to get started with building applications using this framework.

## License

This project is licensed under the MIT License.