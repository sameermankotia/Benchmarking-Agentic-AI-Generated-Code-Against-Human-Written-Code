# Django oracle suite (85 cases)

Specification-derived oracle for the Django URL/view pair (paper §3.3.2). Same
conventions as the Flask oracle: import the SUT via `oracle/conftest.py`, assert
on documented behaviour only.

| File                        | Category           | Cases |
|-----------------------------|--------------------|-------|
| `test_url_resolution.py`    | URL Resolution     | 22    |
| `test_request_object.py`    | Request Object     | 18    |
| `test_view_dispatch.py`     | View Dispatch      | 20    |
| `test_response_handling.py` | Response Handling  | 15    |
| `test_class_based_views.py` | Class-Based Views  | 10    |

The full case set is distributed separately in the replication package.
