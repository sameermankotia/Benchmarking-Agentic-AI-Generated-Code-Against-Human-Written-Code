# Django-pair generation specification

> **PROVENANCE WARNING.** Unlike the Flask specification, this text does not
> appear anywhere in the manuscript or in any earlier version of the
> replication package. The manuscript only *describes* it: "rephrased to
> Django's request and response model", covering five behavioural areas (URL
> resolution, request object behaviour, view dispatch, response handling,
> class-based view behaviour), with templating, application context and
> Blueprints excluded as having no counterpart in the Django URL module.
>
> What follows is a reconstruction from that description, written to match the
> Flask specification's structure, level of detail, and deliberate silences
> (it fixes behaviour and the WSGI interface, and names no API symbols beyond
> those the behaviour requires). **It is not the original.** If the original
> text still exists, replace this file with it before generating, because the
> Django oracle's scope is derived from these five areas.

---

Build a WSGI-compatible URL routing and view dispatching layer in Python 3.11.
The implementation must support: (1) URL resolution from a declared list of
patterns, including literal paths, variable segments with typed converters for
integers, strings, slugs, UUIDs and whole paths, and regular-expression
patterns with named groups; (2) request object encapsulating method, path,
headers, query string, and body, with any segments captured from the URL
passed to the view; (3) view dispatch, in which the first matching pattern's
view is called with the request and the captured segments, and a request
matching no pattern yields a 404; (4) response handling, with a response
object carrying status code, headers, and body; (5) class-based views, in
which a view class dispatches a request to a method named for the HTTP verb,
returns 405 with an `Allow` header for a verb it does not implement, and
serves HEAD from the GET implementation. The implementation must pass a WSGI
compliance check. Provide a complete `pyproject.toml` and a `README.md`.
