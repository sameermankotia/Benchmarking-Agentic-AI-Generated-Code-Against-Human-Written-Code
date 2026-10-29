"""Resolve specification-level roles to whatever a subject actually calls them.

The specification fixes behaviour, the WSGI interface, and four names
(``request``, ``g``, ``current_app``, ``Blueprint``). It does not fix the name
of the application class, the route-registration method, the response class,
or the template-rendering function, so an implementation written from it has
no reason to use Flask's names for any of them.

This module is the declared construction surface: the small set of roles an
oracle suite needs in order to *build* a subject before driving it over WSGI.
Each role resolves in three steps:

1. an explicit per-subject mapping, passed by the correctness runner from the
   ``api_map`` field of ``subjects/subjects.json`` (authoritative, and the
   only mechanism that is guaranteed correct for an arbitrary subject);
2. failing that, a list of conventional candidate names;
3. failing that, a ``RoleUnresolved`` error naming the role and listing what
   the subject does expose, so an unresolved role is a loud failure rather
   than a silent zero score.

Keeping this surface small is the point. Everything a suite asserts *after*
construction goes through WSGI (see ``oracle/wsgi.py``), so no behavioural
assertion depends on a name.
"""

from __future__ import annotations

import inspect
import json
import os
from types import ModuleType

#: role -> conventional names, most conventional first.
CANDIDATES: dict[str, tuple[str, ...]] = {
    # Flask-pair roles.
    "app_class": ("Flask", "Application", "App", "WSGIApplication",
                  "WsgiApplication", "WebApp", "WSGIApp", "Framework",
                  "Server", "Micro"),
    "blueprint_class": ("Blueprint", "BluePrint", "Module", "Router",
                        "Component"),
    "response_class": ("Response", "HttpResponse", "HTTPResponse", "Res"),
    "render_string": ("render_template_string", "render_string",
                      "render_template_str", "render_str", "render"),
    "route": ("route", "add_route", "get_route", "url", "handle", "add"),
    "register_blueprint": ("register_blueprint", "register", "mount",
                           "add_blueprint", "include"),
    # Request accessors. The specification says the request object
    # "encapsulat[es] method, path, headers, query string, and body" but does
    # not fix the attribute names, so each concept is a role.
    "req_method": ("method",),
    "req_path": ("path", "path_info", "url_path"),
    # A request may carry its headers as an HTTP-named mapping, or only in the
    # CGI spelling PEP 3333 delivers them in (``HTTP_X_TEST``, plus
    # ``CONTENT_TYPE`` and ``CONTENT_LENGTH`` without the prefix), which is
    # what Django calls META. The specification requires that the request
    # encapsulate headers, not which of the two spellings it keeps them in, so
    # both are accepted here and `header()` reads either.
    "req_headers": ("headers", "META", "environ"),
    "req_query": ("args", "query", "query_params", "params", "GET",
                  "query_dict"),
    "req_body": ("data", "body", "raw_body", "content", "get_data"),
    # Django-pair roles.
    "url_pattern": ("path", "url", "route", "re_path"),
    "url_pattern_re": ("re_path", "url", "regex_path"),
    "wsgi_handler": ("WSGIHandler", "WsgiHandler", "Handler",
                     "get_wsgi_application", "wsgi_application"),
    "view_base": ("View", "BaseView", "ClassBasedView", "CBV"),
}

#: Roles the specification names outright, reached as plain module attributes.
#: `request` is deliberately NOT here: the specification requires a "request
#: object encapsulating method, path, headers, query string, and body" but
#: never says it is a module-level global, so how a handler obtains it is a
#: convention, not a fixed name. Use `current_request()` instead.
SPEC_NAMED = ("g", "current_app", "Blueprint")


class RoleUnresolved(Exception):
    """A specification-level role has no counterpart on the subject."""


def _load_map() -> dict[str, str]:
    raw = os.environ.get("ORACLE_API_MAP", "").strip()
    if not raw:
        return {}
    try:
        return dict(json.loads(raw))
    except (ValueError, TypeError):
        return {}


class Api:
    """The declared construction surface of one subject."""

    def __init__(self, module, api_map: dict[str, str] | None = None):
        self.mod = module
        self.map = dict(api_map if api_map is not None else _load_map())
        self._cache: dict[str, object] = {}

    # --- resolution -------------------------------------------------------- #

    def name_for(self, role: str, target=None) -> str:  # noqa: D401
        """The attribute name this subject uses for `role`.

        `target` is the object the role lives on. Some roles are module-level
        (the application class, the response class, the renderer) and some are
        methods on an application instance (route registration, blueprint
        registration), so the caller says where to look. The module is always
        tried as a fallback, which covers implementations that expose a
        registrar as a free function instead of a method.
        """
        if role in self.map:
            return self.map[role]
        targets = [t for t in (target, self.mod) if t is not None]
        for candidate in CANDIDATES.get(role, ()):
            if any(hasattr(t, candidate) for t in targets):
                return candidate
        duck = self._duck_typed(role)
        if duck is not None:
            return duck[0]
        raise RoleUnresolved(self._unresolved_message(role, target))

    def _duck_typed(self, role: str):
        """Find a role by shape when no conventional name matched.

        Names are the weakest part of the declared surface: an implementation
        written from the specification may call its application class anything
        (observed: ``FlaskPair``). Rather than grow the candidate list without
        end, the application class is identified by what it does -- it offers
        route registration and is usable as a WSGI callable -- which is
        precisely what the specification requires of it.
        """
        import inspect as _inspect

        if role != "app_class":
            return None
        route_names = CANDIDATES["route"]

        def declares(cls, attr: str) -> bool:
            """Whether `cls` itself defines `attr`.

            `getattr(cls, "__call__")` is true for *every* class, because the
            metaclass supplies it for instantiation. Only an own-namespace
            lookup across the MRO (minus ``object``) distinguishes a class
            that is genuinely callable as a WSGI application.
            """
            return any(attr in base.__dict__ for base in cls.__mro__[:-1])

        found = []
        for name in dir(self.mod):
            if name.startswith("_"):
                continue
            obj = getattr(self.mod, name, None)
            if not _inspect.isclass(obj):
                continue
            route_rank = next((i for i, r in enumerate(route_names)
                               if declares(obj, r)), None)
            if route_rank is None:
                continue
            if not any(declares(obj, w)
                       for w in ("__call__", "wsgi_app", "wsgi")):
                continue
            # Rank by how conventional the route method's name is, so a
            # router helper exposing only `add_route` loses to the
            # application class exposing `route`.
            found.append((route_rank, name, obj))
        if not found:
            return None
        found.sort(key=lambda t: (t[0], len(t[1])))
        return found[0][1], found[0][2]

    def resolve(self, role: str):
        """The object this subject provides for `role`."""
        if role not in self._cache:
            name = self.name_for(role)
            if not hasattr(self.mod, name):
                raise RoleUnresolved(
                    f"subject {self.mod.__name__!r} declares {role!r} as "
                    f"{name!r} (subjects.json api_map) but has no such "
                    f"attribute")
            self._cache[role] = getattr(self.mod, name)
        return self._cache[role]

    def has(self, role: str, target=None) -> bool:
        try:
            self.name_for(role, target)
            return True
        except RoleUnresolved:
            return False

    def _unresolved_message(self, role: str, target=None) -> str:
        shown = target if target is not None else self.mod
        public = sorted(n for n in dir(shown) if not n.startswith("_"))
        where = ("the application instance" if target is not None
                 else "the module")
        return (
            f"cannot resolve the specification role {role!r} on {where} of "
            f"subject {self.mod.__name__!r}.\n"
            f"Tried the conventional names: "
            f"{', '.join(CANDIDATES.get(role, ())) or '(none)'}.\n"
            f"Declare it in subjects/subjects.json under this subject's "
            f"\"api_map\", e.g. \"api_map\": {{\"{role}\": \"<its name>\"}}.\n"
            f"The subject exposes: {', '.join(public[:40])}"
            + (" ..." if len(public) > 40 else ""))

    # --- specification-named module attributes ----------------------------- #

    def __getattr__(self, item):
        # `api.request`, `api.g`, `api.current_app`, `api.Blueprint`.
        if item in SPEC_NAMED:
            try:
                return getattr(self.mod, item)
            except AttributeError as exc:
                raise RoleUnresolved(
                    f"subject {self.mod.__name__!r} does not expose {item!r}, "
                    f"which the specification names explicitly") from exc
        raise AttributeError(item)

    # --- construction ------------------------------------------------------ #

    @staticmethod
    def _call_probing(factory, arg_sets, what: str):
        """Call `factory` with the first argument set its signature accepts.

        Signatures differ between implementations written from the same
        specification (an application class may or may not take an import
        name, a blueprint may or may not take a url prefix at construction).
        Probing keeps that difference out of the test bodies. The sets are
        ordered most-specific first, and the last failure is re-raised so a
        genuine error inside the subject is not mistaken for a signature
        mismatch.
        """
        last: BaseException | None = None
        for args, kwargs in arg_sets:
            try:
                return factory(*args, **kwargs)
            except TypeError as exc:
                # Only a signature mismatch is worth trying the next set.
                if "argument" not in str(exc) and "positional" not in str(exc):
                    raise
                last = exc
        raise RoleUnresolved(
            f"none of the conventional signatures for {what} were accepted by "
            f"{factory!r}: {last}")

    def app(self, **kwargs):
        """A fresh application instance."""
        cls = self.resolve("app_class")
        return self._call_probing(
            cls,
            [((__name__,), kwargs), ((), kwargs)],
            "the application class")

    #: How a variable URL segment is written in a rule string. The
    #: specification requires "variable segments" but does not fix their
    #: syntax, so it is part of the declared surface and overridable per
    #: subject via api_map["var_template"].
    VAR_TEMPLATE = "<{name}>"

    def var(self, name: str) -> str:
        """One variable URL segment, in this subject's rule syntax."""
        return self.map.get("var_template", self.VAR_TEMPLATE).format(name=name)

    def rule(self, *parts: str) -> str:
        """Build a rule from literal parts and ``:name`` variable parts.

        ``api.rule("user", ":name")`` -> ``"/user/<name>"`` by default.
        """
        out = []
        for part in parts:
            out.append(self.var(part[1:]) if part.startswith(":") else part)
        return "/" + "/".join(out)

    def route(self, app, rule: str, methods: list[str] | None = None):
        """Decorator registering a view for `rule` (and optionally `methods`)."""
        name = self.name_for("route", app)
        register = getattr(app, name, None)
        if register is None:
            register = self.resolve("route")   # module-level registrar
            base_args = (app, rule)
        else:
            base_args = (rule,)
        if methods is None:
            return register(*base_args)
        try:
            return register(*base_args, methods=list(methods))
        except TypeError:
            return register(*base_args, list(methods))

    def blueprint(self, name: str, url_prefix: str | None = None):
        """A blueprint, with `url_prefix` applied at construction if supported."""
        cls = self.resolve("blueprint_class")
        kwargs = {} if url_prefix is None else {"url_prefix": url_prefix}
        bp = self._call_probing(
            cls,
            [((name, __name__), kwargs), ((name,), kwargs),
             ((name, __name__), {}), ((name,), {})],
            "the blueprint class")
        # If the prefix could not be given at construction, remember it so
        # `register` can supply it instead.
        if url_prefix is not None and getattr(bp, "url_prefix", None) != url_prefix:
            setattr(bp, "_oracle_prefix", url_prefix)
        return bp

    def register(self, app, bp, url_prefix: str | None = None):
        """Mount `bp` on `app`, under `url_prefix` when one is given.

        Three directions are accepted, because the specification requires
        blueprint-based modularity but not the direction of the call:
        ``app.register_blueprint(bp)``, a module-level ``register(app, bp)``,
        or ``bp.register(app)`` -- the last being how an implementation that
        puts the method on the blueprint does it.

        The prefix is supplied here only if the blueprint is not already
        carrying it. A blueprint that accepted ``url_prefix`` at construction
        (see `blueprint`) owns it, and naming it a second time at registration
        is an error of the oracle's, not the subject's: a registration call
        that takes no prefix argument rejects it with a TypeError, and one
        that concatenates applies it twice. Flask tolerates both because its
        ``register_blueprint(url_prefix=...)`` overrides rather than appends,
        which is a convention of Flask's and not something the specification
        fixes.
        """
        carried = getattr(bp, "url_prefix", None)
        if url_prefix is not None and carried == url_prefix:
            prefix = None
        else:
            prefix = url_prefix or getattr(bp, "_oracle_prefix", None)

        def attempt(fn, base):
            if prefix is None:
                return fn(*base)
            try:
                return fn(*base, url_prefix=prefix)
            except TypeError:
                return fn(*base, prefix)

        # 1. a method on the application
        try:
            name = self.name_for("register_blueprint", app)
            fn = getattr(app, name, None)
            if fn is not None:
                return attempt(fn, (bp,))
            # 2. a free function in the module
            return attempt(self.resolve("register_blueprint"), (app, bp))
        except RoleUnresolved:
            pass

        # 3. a method on the blueprint, taking the application
        for name in CANDIDATES["register_blueprint"] + ("attach", "bind"):
            fn = getattr(bp, name, None)
            if callable(fn):
                return attempt(fn, (app,))
        raise RoleUnresolved(
            f"subject {self.mod.__name__!r} offers no way to mount a "
            f"blueprint on an application: neither the application nor the "
            f"module nor the blueprint exposes a registration call. The "
            f"specification requires Blueprint-based modular applications "
            f"with URL prefix inheritance.")

    def render(self, source: str, **context):
        """Render `source` as a template with `context`."""
        return self.resolve("render_string")(source, **context)

    def response(self, body="", status: int = 200,
                 headers: dict | None = None):
        """A response object carrying `body`, `status`, and `headers`."""
        cls = self.resolve("response_class")
        sets = [
            ((body,), {"status": status, "headers": headers or {}}),
            ((body,), {"status_code": status, "headers": headers or {}}),
            ((body,), {"status": status}),
            ((body,), {}),
        ]
        resp = self._call_probing(sets and cls, sets, "the response class")
        if headers:
            for key, value in headers.items():
                try:
                    resp.headers[key] = value
                except (AttributeError, TypeError):
                    pass
        try:
            if resp.status_code != status:
                resp.status_code = status
        except (AttributeError, TypeError):
            pass
        return resp

    # --- obtaining the in-flight request ----------------------------------- #

    @staticmethod
    def _looks_like_request(obj) -> bool:
        """Whether `obj` plausibly is a request object.

        Checked by behaviour, not by type or name. Modules are excluded
        explicitly: a package exporting a `Request` class from a submodule
        called `request` leaves `mod.request` bound to the *module*, which is
        a trap worth naming rather than silently mis-resolving.
        """
        if obj is None or isinstance(obj, ModuleType):
            return False
        return sum(hasattr(obj, a) for a in ("method", "path", "headers")) >= 2

    def current_request(self, view_args: tuple = ()):
        """The request for the call in flight, however this subject delivers it.

        Three conventions are accepted, because the specification fixes the
        request's *content* and not the route by which a handler reaches it:

        1. passed to the handler (the first argument that looks like a request);
        2. a module-level object, conventionally ``request``;
        3. hung off the application or request context.

        If none of them yields a request, the subject gives a handler no way to
        see the request it is handling, which is a specification failure and is
        reported as one.
        """
        for candidate in view_args:
            if self._looks_like_request(candidate):
                return candidate
        for name in ("request", "req"):
            if self._looks_like_request(getattr(self.mod, name, None)):
                return getattr(self.mod, name)
        for holder_name in ("current_app", "g"):
            holder = getattr(self.mod, holder_name, None)
            if holder is None:
                continue
            for attr in ("request", "req", "_request"):
                try:
                    obj = getattr(holder, attr, None)
                except Exception:                          # noqa: BLE001
                    continue
                if self._looks_like_request(obj):
                    return obj
        raise RoleUnresolved(
            f"subject {self.mod.__name__!r} gives a handler no way to reach "
            f"the request it is handling: nothing was passed to it, no "
            f"module-level request object exists, and neither current_app nor "
            f"g carries one. The specification requires a request object "
            f"encapsulating method, path, headers, query string and body.")

    # --- request accessors ------------------------------------------------- #

    def _req_attr(self, req, role: str):
        name = self.name_for(role, req)
        value = getattr(req, name)
        # Some implementations expose the body as a method (get_data()).
        return value() if callable(value) and role == "req_body" else value

    def method(self, req) -> str:
        return str(self._req_attr(req, "req_method")).upper()

    def path(self, req) -> str:
        return str(self._req_attr(req, "req_path"))

    @staticmethod
    def _header_spellings(name: str) -> tuple[str, ...]:
        """Every spelling under which `name` may be stored, most direct first.

        A request that keeps its headers in the CGI form PEP 3333 hands it
        (Django's META) stores ``X-Test`` as ``HTTP_X_TEST``, and the two
        entity headers without the prefix at all. Both are the same header,
        so both spellings are looked for.
        """
        cgi = name.upper().replace("-", "_")
        if cgi in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            return (name, cgi, f"HTTP_{cgi}")
        return (name, f"HTTP_{cgi}")

    def header(self, req, name: str, default: str = "") -> str:
        """One request header, read case-insensitively and spelling-agnostically."""
        headers = self._req_attr(req, "req_headers")
        wanted = self._header_spellings(name)
        getter = getattr(headers, "get", None)
        if callable(getter):
            for spelling in wanted:
                try:
                    value = getter(spelling)
                except TypeError:
                    break
                if value is not None:
                    return str(value)
        lowered = {s.lower() for s in wanted}
        try:
            for key in headers:
                if str(key).lower() in lowered:
                    return str(headers[key])
        except TypeError:
            return default
        return default

    def query_get(self, req, name: str, default: str = "") -> str:
        """One query-string parameter."""
        params = self._req_attr(req, "req_query")
        try:
            value = params.get(name)
        except AttributeError:
            return default
        if value is None:
            return default
        # Some implementations return every value for a key.
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else default
        return str(value)

    def body_bytes(self, req) -> bytes:
        """The raw request body."""
        value = self._req_attr(req, "req_body")
        if isinstance(value, str):
            return value.encode("utf-8")
        return bytes(value or b"")

    # --- introspection used by the suites' skip conditions ----------------- #

    def accepts_methods_kwarg(self, app) -> bool:
        """Whether this subject's route registration takes a `methods` keyword."""
        try:
            name = self.name_for("route", app)
            sig = inspect.signature(getattr(app, name))
        except (TypeError, ValueError, AttributeError, RoleUnresolved):
            return True
        return "methods" in sig.parameters
