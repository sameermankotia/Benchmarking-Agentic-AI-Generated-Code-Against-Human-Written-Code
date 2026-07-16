"""Templating — 15 oracle cases (paper §3.3.1).

Spec area (4): Jinja2 template rendering integrated with the application
context.
"""

from __future__ import annotations

import pytest


def _render(app, fw, tmpl, **ctx):
    @app.route("/t")
    def t():
        return fw.render_template_string(tmpl, **ctx)
    return app.test_client().get("/t").data.decode()


def test_render_plain_string(app, fw):
    assert _render(app, fw, "hello") == "hello"


def test_render_variable(app, fw):
    assert _render(app, fw, "Hi {{ name }}", name="Sam") == "Hi Sam"


def test_render_arithmetic(app, fw):
    assert _render(app, fw, "{{ 2 + 3 }}") == "5"


def test_render_conditional_true(app, fw):
    assert _render(app, fw, "{% if x %}yes{% else %}no{% endif %}", x=True) == "yes"


def test_render_conditional_false(app, fw):
    assert _render(app, fw, "{% if x %}yes{% else %}no{% endif %}", x=False) == "no"


def test_render_loop(app, fw):
    out = _render(app, fw, "{% for i in items %}{{ i }}{% endfor %}", items=[1, 2, 3])
    assert out == "123"


def test_render_filter_upper(app, fw):
    assert _render(app, fw, "{{ s|upper }}", s="abc") == "ABC"


def test_render_filter_length(app, fw):
    assert _render(app, fw, "{{ items|length }}", items=[1, 2, 3, 4]) == "4"


def test_render_dict_access(app, fw):
    assert _render(app, fw, "{{ d['k'] }}", d={"k": "v"}) == "v"


def test_render_attribute_access(app, fw):
    class Obj:
        val = "attr"
    assert _render(app, fw, "{{ o.val }}", o=Obj()) == "attr"


def test_render_autoescape_html(app, fw):
    out = _render(app, fw, "{{ s }}", s="<script>")
    assert "&lt;script&gt;" in out


def test_render_safe_filter(app, fw):
    out = _render(app, fw, "{{ s|safe }}", s="<b>x</b>")
    assert out == "<b>x</b>"


def test_render_nested_loop_conditional(app, fw):
    tmpl = "{% for i in xs %}{% if i > 1 %}{{ i }}{% endif %}{% endfor %}"
    assert _render(app, fw, tmpl, xs=[1, 2, 3]) == "23"


def test_render_default_filter(app, fw):
    assert _render(app, fw, "{{ missing|default('D') }}") == "D"


def test_render_uses_app_context_url_for(app, fw):
    @app.route("/target")
    def target():
        return "t"

    @app.route("/link")
    def link():
        return fw.render_template_string("{{ url_for('target') }}")
    assert app.test_client().get("/link").data == b"/target"
