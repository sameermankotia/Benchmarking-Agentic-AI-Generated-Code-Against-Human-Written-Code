"""Templating — oracle cases for specification area (4).

"Jinja2 template rendering integrated with the application context."

Rendering goes through the resolved renderer role (`api.render`). Because the
specification names Jinja2, Jinja2's own syntax is specified behaviour and is
asserted on directly; what is *not* specified is the renderer's name, which is
why it is resolved rather than imported.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def rendered(api, route, app, get):
    """Render `source` with `context` inside a request, return the body text."""
    counter = {"n": 0}

    def _rendered(source, **context):
        counter["n"] += 1
        path = f"/tpl{counter['n']}"

        def view(**_params):
            return api.render(source, **context)
        view.__name__ = f"tpl_{counter['n']}"
        route(path)(view)
        return get(path).text
    return _rendered


# --- Basic: rendering happens ---------------------------------------------- #

def test_renders_literal_text(rendered):
    assert "plain text" in rendered("plain text")


def test_renders_a_variable(rendered):
    assert "world" in rendered("hello {{ name }}", name="world")


def test_renders_multiple_variables(rendered):
    out = rendered("{{ a }}-{{ b }}", a="x", b="y")
    assert "x-y" in out


def test_variable_not_left_in_output(rendered):
    assert "{{" not in rendered("value: {{ v }}", v="substituted")


# --- Behavioural: Jinja2 constructs ---------------------------------------- #

def test_renders_a_for_loop(rendered):
    out = rendered("{% for i in items %}{{ i }},{% endfor %}",
                   items=[1, 2, 3])
    assert "1,2,3," in out


def test_renders_a_conditional_true_branch(rendered):
    out = rendered("{% if flag %}yes{% else %}no{% endif %}", flag=True)
    assert "yes" in out and "no" not in out


def test_renders_a_conditional_false_branch(rendered):
    out = rendered("{% if flag %}yes{% else %}no{% endif %}", flag=False)
    assert "no" in out


def test_renders_a_filter(rendered):
    assert "SHOUT" in rendered("{{ word|upper }}", word="shout")


def test_renders_dict_access(rendered):
    assert "inner" in rendered("{{ d['k'] }}", d={"k": "inner"})


def test_renders_attribute_access(rendered):
    class Obj:
        attr = "got-attr"
    assert "got-attr" in rendered("{{ o.attr }}", o=Obj())


def test_renders_nested_loop_and_conditional(rendered):
    out = rendered(
        "{% for i in items %}{% if i > 1 %}{{ i }}{% endif %}{% endfor %}",
        items=[1, 2, 3])
    assert "23" in out


def test_renders_arithmetic_expression(rendered):
    assert "7" in rendered("{{ 3 + 4 }}")


# --- Integration with the request and application context ------------------ #

def test_rendered_output_becomes_the_response_body(api, route, get):
    def view(**_):
        return api.render("in-response")
    route("/ir")(view)
    result = get("/ir")
    assert result.status_code == 200 and b"in-response" in result.body


def test_renders_inside_a_request_with_request_data(api, route, get):
    req = api.request

    def view(**_):
        return api.render("path={{ p }}", p=api.path(req))
    route("/withreq")(view)
    assert b"path=/withreq" in get("/withreq").body


def test_autoescapes_html_in_a_variable(rendered):
    """Jinja2's autoescaping is on for HTML templates in a web framework."""
    out = rendered("{{ danger }}", danger="<script>x</script>")
    assert "<script>" not in out or "&lt;script&gt;" in out
