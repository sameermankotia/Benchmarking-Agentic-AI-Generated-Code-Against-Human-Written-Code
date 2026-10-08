# Flask-pair oracle suite

Specification-derived oracle for the Flask pair. Tests construct a subject
through the declared role surface (`oracle/api.py`) and then drive it over its
**WSGI interface** (`oracle/wsgi.py`), so the same suite runs against Flask,
the SWE-agent framework, and the OpenHands framework without naming any of
them.

| File                         | Category           | Functions | Cases |
|------------------------------|--------------------|----------:|------:|
| `test_url_routing.py`        | URL Routing        |        23 |    30 |
| `test_request_handling.py`   | Request Handling   |        20 |    28 |
| `test_response_rendering.py` | Response Rendering |        18 |    24 |
| `test_templating.py`         | Templating         |        15 |    15 |
| `test_app_context.py`        | App Context        |        21 |    21 |
| `test_blueprints.py`         | Blueprints         |        20 |    22 |
| **Total**                    |                    |   **117** |**140**|

"Cases" is the count after `pytest` parametrisation, which is what the
correctness stage reports. Flask 3.0.3 passes 140/140 with no skips.

## Why WSGI

The specification fixes behaviour, the WSGI interface ("must pass a WSGI
compliance check"), and exactly four names: `request`, `g`, `current_app`, and
`Blueprint`. It does not fix the name of the application class, the route
decorator, the response class, or the template renderer. An implementation
written from it therefore has no reason to use Flask's names, so a suite that
asserts through a framework-specific test client is a conformance suite for
that framework rather than an oracle for the specification.

Every assertion here is made on a WSGI status line, response header, or
response body. `grep` the test files for `Flask`, `test_client`, `url_for`,
`jsonify` or `render_template`: there are no matches.

## Declared construction surface

Six roles are needed to *build* a subject before driving it. Each resolves
from the subject's `api_map` in `subjects/subjects.json` first, then from
conventional candidate names, and otherwise raises `RoleUnresolved` naming the
role — an unresolved role is a loud failure, never a silent zero.

| Role                 | Default candidates                              |
|----------------------|-------------------------------------------------|
| `app_class`          | `Flask`, `Application`, `App`, `WSGIApplication`, … |
| `route`              | `route`, `add_route`, `url`, `handle`, `add`    |
| `blueprint_class`    | `Blueprint`, `Module`, `Router`, `Component`     |
| `register_blueprint` | `register_blueprint`, `register`, `mount`, …    |
| `response_class`     | `Response`, `HttpResponse`, `Res`               |
| `render_string`      | `render_template_string`, `render_string`, …    |

Request attributes are resolved the same way (`req_method`, `req_path`,
`req_headers`, `req_query`, `req_body`), because the specification names the
concepts — "method, path, headers, query string, and body" — but not the
attribute names. Variable-segment syntax is `var_template` (default
`<{name}>`).

## Scope

The suite asserts only on behaviour the specification fixes. Deliberately out
of scope, and therefore absent: request/response lifecycle hooks, error
handlers, typed URL converters, form parsing, cookie handling, URL building,
and anything reached through a private attribute. Each omission is a thing the
specification does not mention, so requiring it would penalise a subject for
not having guessed Flask.
