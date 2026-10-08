# Django-pair oracle suite

Specification-derived oracle for the Django pair, covering URL resolution,
request-object behaviour, view dispatch, response handling, and class-based
views. As in the Flask pair, subjects are constructed through a declared role
surface and then driven over **WSGI** (`oracle/wsgi.py`).

| File                        | Category           | Functions | Cases |
|-----------------------------|--------------------|----------:|------:|
| `test_url_resolution.py`    | URL Resolution     |        22 |    25 |
| `test_request_object.py`    | Request Object     |        19 |    26 |
| `test_view_dispatch.py`     | View Dispatch      |        19 |    22 |
| `test_response_handling.py` | Response Handling  |        15 |    21 |
| `test_class_based_views.py` | Class-Based Views  |        10 |    10 |
| **Total**                   |                    |    **85** |**104**|

The Django 5.0.6 URL module passes 104/104 with no skips.

## Why WSGI

A URL resolves if and only if a request to it reaches the intended view, so
resolution is asserted through the WSGI response rather than by calling a
resolver API. This is what makes the suite an oracle for the specification
rather than for Django: **no test file imports `django`**. The previous version
of this suite hard-imported `django.urls`, `django.http`, `django.views` and
`django.views.decorators.*` by literal module path in all five files, which
meant it could only ever run against Django itself.

## Declared construction surface

| Role             | Resolved from (first match)                                  |
|------------------|--------------------------------------------------------------|
| `url_pattern`    | `urls.path`, `urls.url`, `urls.route`, `path`                 |
| `url_pattern_re` | `urls.re_path`, `urls.url`, `re_path`                         |
| `wsgi_handler`   | `core.handlers.wsgi.WSGIHandler`, `WSGIHandler`, `core.wsgi.get_wsgi_application`, … |
| `response_class` | `http.HttpResponse`, `http.Response`, `HttpResponse`, `Response` |
| `view_base`      | `views.View`, `views.generic.View`, `View`                    |

A subject that wires these differently declares them under its `api_map` in
`subjects/subjects.json`. The suite also needs a settings object to configure
before import (`conf.settings` or `settings`); the configuration it supplies
is minimal — templating only, with no installed applications, database, or
middleware — and the template backend path is derived from the subject's own
package name rather than hard-coded.

Each `serve(...)` call builds a freshly named URL configuration, so a
subject's resolver cache cannot carry state between tests.

## Scope

Out of scope, because the specification does not fix them: middleware,
sessions, authentication, ORM access, template-directory discovery, URL
reversing, and the framework's own debug pages (hence no assertion on what is
served for an empty URL configuration).
