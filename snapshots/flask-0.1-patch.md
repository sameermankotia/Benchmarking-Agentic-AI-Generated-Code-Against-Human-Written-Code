# Patch applied to this snapshot

`flask.py` in the `0.1` tag (commit `8605cc3`) uses Python 2's
`except X, e:` clause syntax, which is a `SyntaxError` under Python 3 and
cannot be parsed by any tool in this pipeline (Radon, complexipy, pylint,
Bandit all parse via Python 3's `ast`). Two occurrences were rewritten to
the Python 3 `except X as e:` form so the file is analyzable under the
same Python 3.11 toolchain used for every other subject:

```diff
- except HTTPException, e:
+ except HTTPException as e:
```
(`flask.py`, originally line 545)

```diff
- except Exception, e:
+ except Exception as e:
```
(`flask.py`, originally line 550)

No other change was made. This is a syntactic rewrite only (identical
control flow, identical exception binding); it does not alter behavior.
Diff against the pinned upstream commit (`snapshots/MANIFEST.txt`) to
verify.
