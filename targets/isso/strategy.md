# Test strategy for isso

isso is a comment server: a WSGI application built on werkzeug with a JSON HTTP API (`GET /`,
`POST /new`, `GET`/`PUT`/`DELETE /id/<id>`, `/count`, `/latest`, and so on). Its JavaScript client
has its own Jest tests; there are no Python browser tests. This file is the rule the test writer
follows.

## Where new tests go

- **API level, all of the coverage.** `isso/tests/test_<feature>_api.py`. Tests call the service
  through werkzeug's test client, the way `isso/tests/test_comments.py` does: build the app in
  `setUp` from `config.load(config.default_file())` with a temporary database file, the guard off
  (`conf.set("guard", "enabled", "off")`, or its rate limit rejects the second post), an
  `App(Isso, core.Mixin)` class, `FakeIP` around `wsgi_app`, and `JSONClient(self.app, Response)`.
  Copy the module-level `http.curl = curl` line from `test_comments.py`: it is the suite's own way
  of keeping the server from fetching the commented page over the network.
  Reason: the HTTP API is the public surface; the client fixtures exercise it without a network.
- **No browser tests.** isso has no Python browser tests and the writer adds none.
- **Unit tests belong to the implementer.** The test writer does not add them.
- Every placement decision is written down with its reason.

## Helpers

isso has no `helpers.py`. Its test helpers are in `isso/tests/fixtures.py`: `JSONClient` (a
werkzeug `Client` that sends JSON), `FakeIP` (sets the remote address), `FakeHost`, `curl`, and
`loads` (decodes a response body as JSON). Test files import them as `from fixtures import ...`.

## How tests are written

- The application's conventions win over generic pytest style: `unittest.TestCase` classes, a
  temporary database per test in `setUp`, `JSONClient`, and requests with the query string spelled
  out (`/new?uri=%2Fpath%2F`).
- A comment's author gets an edit cookie named after the comment id when posting it; the same
  `JSONClient` sends it back, which `GET`, `PUT` and `DELETE /id/<id>` require.
- Tests use the public surface: routes, query parameters, JSON bodies, status codes and response
  headers, with expected values written out literally. They never import the code's constants.
- A test must fail on the code before the change, and for a behavioural reason, not a missing name.
- No sleeps. No network. No mocking of the application's own code.

## Running the suite

Use the repository's virtual environment from the repository root, with `python -m pytest` so the
checked-out code is the code imported:

```
python -m pytest -p no:cacheprovider --doctest-modules isso
python -m pytest -p no:cacheprovider isso/tests/<file>
```
