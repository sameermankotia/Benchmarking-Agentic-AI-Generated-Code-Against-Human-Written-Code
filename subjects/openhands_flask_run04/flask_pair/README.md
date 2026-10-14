# Flask Pair

Flask Pair is a WSGI-compatible micro web framework built in Python 3.11. It provides essential features for web development, including:

1. URL routing with variable segments and HTTP method filtering.
2. Request object encapsulating method, path, headers, query string, and body.
3. Response object with status code, headers, and body.
4. Jinja2 template rendering integrated with the application context.
5. Application context management using thread-local storage.
6. Blueprint-based modular applications with URL prefix inheritance.

## Installation

Install Flask Pair using pip:

```bash
pip install flask_pair
```

## Usage

```python
from flask_pair import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask Pair!"

if __name__ == '__main__':
    app.run()
```

## Development

To contribute to Flask Pair, clone the repository and install dependencies:

```bash
git clone <repository-url>
cd flask_pair
pip install -e .
```

Run tests with:

```bash
pytest
```
