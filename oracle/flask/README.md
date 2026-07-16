# Flask oracle suite (120 cases)

This directory holds the specification-derived oracle test suite for the Flask
pair (paper §3.3.1). Tests import the system-under-test through the canonical
name provided by `oracle/conftest.py` and assert on documented **behaviour**,
never on implementation-specific symbols, so the same suite runs against Flask,
the SWE-agent framework, and the OpenHands framework.

Split the cases across these files so the runner buckets them into the paper's
categories automatically:

| File                        | Category            | Cases |
|-----------------------------|---------------------|-------|
| `test_url_routing.py`       | URL Routing         | 25    |
| `test_request_handling.py`  | Request Handling    | 20    |
| `test_response_rendering.py`| Response Rendering  | 18    |
| `test_templating.py`        | Templating          | 15    |
| `test_app_context.py`       | App Context         | 22    |
| `test_blueprints.py`        | Blueprints          | 20    |

The full case set is out of scope for the harness build and is distributed
separately in the replication package.
