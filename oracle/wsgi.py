"""Drive a subject through its WSGI interface (PEP 3333).

The specification given to every agentic system fixes exactly one interface:
the implementation "must pass a WSGI compliance check". Every behavioural
assertion in both oracle suites is therefore made by calling the subject as a
WSGI callable and inspecting the status line, the response headers, and the
response body -- never through a framework-specific test client, response
wrapper, or routing table.

This is what makes one suite portable across implementations that share no
API names. It also means the suite asserts only on behaviour the
specification actually fixes.
"""

from __future__ import annotations

import io
import json as _json
from dataclasses import dataclass, field
from urllib.parse import urlencode


@dataclass
class WsgiResult:
    """What a WSGI call returned, in specification terms."""

    status: str
    headers: list[tuple[str, str]]
    body: bytes
    #: Populated when the application raised instead of returning.
    exc: BaseException | None = field(default=None)

    @property
    def status_code(self) -> int:
        return int(self.status.split(" ", 1)[0])

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")

    def header(self, name: str, default: str = "") -> str:
        """First header matching `name`, case-insensitively."""
        lowered = name.lower()
        for key, value in self.headers:
            if key.lower() == lowered:
                return value
        return default

    def header_all(self, name: str) -> list[str]:
        lowered = name.lower()
        return [v for k, v in self.headers if k.lower() == lowered]

    def json(self):
        return _json.loads(self.text)


def build_environ(
    method: str = "GET",
    path: str = "/",
    *,
    query: str | dict | None = None,
    headers: dict | None = None,
    body: bytes | str | None = None,
    content_type: str | None = None,
    scheme: str = "http",
    host: str = "testserver",
) -> dict:
    """A minimal PEP 3333 environ.

    Only the keys PEP 3333 requires, plus the ones the specification's request
    object is said to encapsulate (method, path, headers, query string, body).
    """
    if isinstance(query, dict):
        query = urlencode(query, doseq=True)
    if isinstance(body, str):
        body = body.encode("utf-8")
    body = body or b""

    environ = {
        "REQUEST_METHOD": method.upper(),
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": query or "",
        "SERVER_NAME": host,
        "SERVER_PORT": "80" if scheme == "http" else "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "HTTP_HOST": host,
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": scheme,
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "CONTENT_LENGTH": str(len(body)),
    }
    if content_type:
        environ["CONTENT_TYPE"] = content_type
    for name, value in (headers or {}).items():
        key = "HTTP_" + name.upper().replace("-", "_")
        if name.lower() == "content-type":
            environ["CONTENT_TYPE"] = value
        elif name.lower() == "content-length":
            environ["CONTENT_LENGTH"] = value
        else:
            environ[key] = value
    return environ


def call(app, method: str = "GET", path: str = "/", **kwargs) -> WsgiResult:
    """Call `app` as a WSGI application and collect the response.

    Exercises the parts of PEP 3333 an application must support: the
    `start_response` callback, an iterable response body, and `close()` on
    that iterable when it provides one.
    """
    environ = build_environ(method, path, **kwargs)
    captured: dict = {}

    def start_response(status, response_headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = list(response_headers)
        if exc_info:
            captured["exc_info"] = exc_info
        return lambda data: None     # PEP 3333 write() callable

    try:
        iterable = app(environ, start_response)
        try:
            chunks = [c for c in iterable if c]
        finally:
            if hasattr(iterable, "close"):
                iterable.close()
    except BaseException as exc:                      # noqa: BLE001
        return WsgiResult(
            status=captured.get("status", "500 Internal Server Error"),
            headers=captured.get("headers", []),
            body=b"",
            exc=exc,
        )

    for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise AssertionError(
                "WSGI violation: response iterable yielded "
                f"{type(chunk).__name__}, not bytes")

    return WsgiResult(
        status=captured.get("status", ""),
        headers=captured.get("headers", []),
        body=b"".join(chunks),
    )


def json_body(payload) -> tuple[bytes, str]:
    """A JSON request body and its content type."""
    return _json.dumps(payload).encode("utf-8"), "application/json"


def form_body(fields: dict) -> tuple[bytes, str]:
    """A URL-encoded form body and its content type."""
    return (urlencode(fields, doseq=True).encode("utf-8"),
            "application/x-www-form-urlencoded")
