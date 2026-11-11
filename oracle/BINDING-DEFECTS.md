# Binding defects found while scoring the agentic subjects

A specification-derived oracle can fail a working framework for a convention
the specification never fixes. Every time that happened while the 15 agentic
subjects were scored it is recorded here, with what the oracle had assumed,
which subject exposed it, what the fix was, and what it moved. Nine defects,
all fixed in the committed suites: eight in the oracle's binding (1 to 5 and
7 to 9) and one in the analysis stage's scope filter (6), which the paper
reports separately.

The control for every one of them is the pair of human baselines: Flask 3.0.3
held at **140/140** and the Django URL module at **104/104** through all nine
changes. A fix that moved a baseline would have been a change to what the
suite tests, not a correction to how it binds. This shows that no fix narrowed
what the oracle accepts from an implementation that follows the
specification. It does not show that a widened binding can never accept
behaviour outside it; every fix only changes how a subject is constructed and
how its request and response are read, never an asserted status, header or
body.

A defect is listed here only where the specification is genuinely silent. Where
the specification does fix the behaviour, a failure stays a failure: see
"Not defects" below.

| # | The oracle assumed | Exposed by | Now |
|---|--------------------|------------|-----|
| 1 | the application class is findable by name | `FlaskPair` (OpenHands) | also resolved by shape: the class that registers routes and is callable as a WSGI application (`oracle/api.py`, `_duck_typed`) |
| 2 | a view receives nothing positionally | SWE-agent and OpenHands subjects that pass the request | every oracle view is `def view(*_req, **params)`, and `api.current_request(view_args)` reads the request from whichever route it arrived by |
| 3 | blueprints are mounted by the application | OpenHands subjects with `bp.register(app)` | three directions accepted: on the application, as a module-level function, or on the blueprint |
| 4 | response headers are set Django's way, `resp[name] = value` | agentic Django subjects exposing only a `headers` mapping | item assignment, a `.headers` mapping, or `set_header`/`add_header` (`oracle/django/conftest.py`, `set_header`) |
| 5 | a Django-shaped subject has settings and reads `ROOT_URLCONF` | agentic Django subjects whose WSGI factory takes the patterns directly | both wirings accepted; only a signature rejection falls through to the settings route |
| 6 | an `include` scope filter matches the first path component | every OpenHands subject (`flask_pair/flask_pair`, `flask_pair_framework/src/flask_pair_framework`) | matched as a path prefix (`analysis/common.py`). Until then **all five OpenHands subjects measured zero files** |
| 7 | URL patterns are written without a leading slash, Django's spelling | `swe_django_run01`, whose resolver matches the raw `PATH_INFO` | the spelling is probed once per session and applied by the `pattern` fixture. This alone moved `swe_django_run01` from 12.5% to 95.2% |
| 8 | the request keeps its headers in an attribute named `headers` | `swe_django_run01`, `swe_django_run03`, which keep them only in `META`, the CGI spelling PEP 3333 delivers | `req_headers` resolves `headers`, `META` or `environ`, and `api.header()` reads either spelling, including `CONTENT_TYPE`/`CONTENT_LENGTH` without the `HTTP_` prefix. Moved those two runs from 95.2% to 99.0% and from 96.2% to 100.0%, and the configuration's median from 96.2% to 100.0% |
| 9 | a blueprint's URL prefix can be named twice, at construction and again at registration | `openhands_flask_run01`, `openhands_flask_run05`, whose `register(app)` takes no prefix and applies the one the blueprint already holds | the prefix is passed to the registration call only when the blueprint is not already carrying it. Flask tolerated the double naming because its `register_blueprint(url_prefix=...)` overrides rather than appends, which is a convention of Flask's. Moved `openhands_flask_run05` from 19.3% to 20.7%, and the configuration's maximum from 20.0% to 20.7% |

Defects 1-7 were found in the first scoring pass, 8 and 9 in the audit of that
pass; the pass rates in `results/correctness/` are the ones measured after all
nine.

## Not fixed, and reported as bounds

Four things that look like the same class of problem and were left failing.
The paper reports a bound for the two that change a configuration's score.

- **String templates.** The templating cases render template strings, but the
  specification only asks for Jinja2 rendering. `swe_flask_run03` and
  `swe_flask_run05` offer only file-based rendering by template name and fail
  13 of the 15 templating cases for that reason. Counting all 13 as passes
  would raise those two runs to at most 75.7% and the configuration median to
  at most 75.0%.
- **`swe_django_run01`'s regex patterns.** Its `path()` matches the raw
  `PATH_INFO` and so needs a leading slash (defect 7), but its `re_path()`
  compiles the regex it is handed and is anchored at the start, so the two
  spellings of the same framework disagree. The oracle applies the probed
  prefix to `path()` only; the regex case stays failing, which is why that run
  scores 103/104 rather than 104/104. It is an inconsistency inside the
  subject, not an assumption of the oracle's.
- **A view returning a plain string.** Several OpenHands subjects require a
  view to return their response object and raise `TypeError` on a string. The
  oracle's views return strings in places, which is Flask's convenience and
  not something the specification fixes, so this is arguably a tenth defect.
  It is listed here rather than fixed because the specification does require a
  response object and says nothing about a string shortcut, so neither
  behaviour can be called the specified one, and changing it would widen the
  construct rather than correct a binding. Measured effect, with the oracle's
  views wrapped so that a string they return is converted into the subject's
  own response class (`Api.response`): `openhands_flask_run01` 15.0% to 52.1%,
  `run02` 20.0% to 50.0%, `run05` 20.7% to 46.4%, `run03` and `run04`
  unchanged, so the OpenHands median moves from 15.0% to 46.4%. Every SWE-agent
  Flask run and the Flask baseline (140/140) are unchanged. The paper reports
  this as a bound.
- **Autoescaping.** `test_autoescapes_html_in_a_variable` passes vacuously
  against a subject whose rendering fails outright: an empty body contains no
  unescaped markup. The case is kept as written because tightening it would
  change the measured pass rates, and the property it is meant to check is
  measured directly instead, at the Jinja2 `Environment` construction, by
  `analysis/paper_numbers.py` (`rq4_security.jinja2_autoescaping`): eight of
  the ten Flask-specification runs create a Jinja2 environment, and five of
  those eight leave autoescaping off. Bandit flags all five (B701).
