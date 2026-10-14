# Flask-pair generation specification

Given verbatim to every agentic system for the Flask pair. Reproduced exactly
as it appears in the manuscript (Section III-B4). Do not edit: the oracle
suite's scope is derived from these six numbered areas, and changing the
wording changes what RQ1 measures.

---

Build a WSGI-compatible micro web framework in Python 3.11. The framework must
support: (1) URL routing with variable segments and HTTP method filtering;
(2) request object encapsulating method, path, headers, query string, and
body; (3) response object with status code, headers, and body; (4) Jinja2
template rendering integrated with the application context; (5) application
context management using thread-local storage so that `current_app` and `g`
are accessible within a request; (6) Blueprint-based modular applications with
URL prefix inheritance. The implementation must pass a WSGI compliance check
and include a built-in development server. Provide a complete
`pyproject.toml` and a `README.md`.
