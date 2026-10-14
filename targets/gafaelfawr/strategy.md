# Test strategy for gafaelfawr

gafaelfawr is an authentication and authorization service built on FastAPI. Its public surface is
HTTP: the REST API under `/auth/api/v1/` (tokens, users, OpenID Connect clients, quotas, history)
and the ingress and login routes. It has no Python browser tests. This file is the rule the test
writer follows.

## Where new tests go

- **API level, all of the coverage.** `tests/handlers/test_<feature>_api.py`. Tests call the
  service through the suite's `client` fixture (an httpx `AsyncClient` bound to the app), the way
  `tests/handlers/api_oidc_test.py` and `tests/handlers/api_tokens_test.py` do. Reason: the HTTP API
  is the public surface; the fixture exercises it without a network.
- **No browser tests.** gafaelfawr has none and the writer adds none.
- **Unit tests belong to the implementer.** The test writer does not add them.
- Every placement decision is written down with its reason.

## Helpers and fixtures

gafaelfawr has no `helpers.py`. Its test helpers are in `tests/support/`:
`tests/support/tokens.py` has `create_session_token(factory, username=..., scopes={...})`, which
makes a user's session token and returns its `TokenData` (`.token` for the `Authorization: Bearer`
header, `.username`); `tests/support/cookies.py` has `set_session_cookie(client, token)` (returns
the CSRF token to send as `X-CSRF-Token`) and `clear_session_cookie`; `tests/support/constants.py`
has `TEST_HOSTNAME`. Fixtures come from `tests/conftest.py`: `client`, `factory`, `mock_slack`, and
`config`, chosen per test with `@pytest.mark.parametrize("config", ["<name>"], indirect=True)` from
`tests/data/config/<name>.yaml`; use the configuration the existing tests of the same routes use.

`tests` is a package. Test files import helpers relatively, as the existing tests do:
`from ..support.tokens import create_session_token`. Never `from tests.support ...` and never
`sys.path` changes.

## How tests are written

- The application's conventions win over generic pytest style: module-level `async def` tests with
  `@pytest.mark.asyncio` (the suite runs pytest-asyncio in strict mode), the `client` and `factory`
  fixtures, and full route paths (`/auth/api/v1/...`).
- Postgres and Redis are started by the suite itself (testcontainers, session-scoped); a test never
  starts or stubs them.
- Tests use the public surface: routes, JSON bodies, status codes and headers, with expected values
  written out literally. They never import the code's constants or call its services to check a
  result; reading back through a `GET` is the check.
- Timestamps in responses are ISO 8601 strings; compare them as `datetime.fromisoformat(...)`
  values against times taken in the test, never with a sleep.
- A test must fail on the code before the change, and for a behavioural reason, not a missing name.
- No sleeps. No network. No mocking of the application's own code.

## Running the suite

From the repository root with the environment's `python`, its `bin` folder first on PATH (some
tests run `alembic`) and Docker running. `-o "pythonpath=src client/src"` makes a worktree import
its own code:

```
python -m pytest -p no:cacheprovider -o "pythonpath=src client/src" tests
python -m pytest -p no:cacheprovider -o "pythonpath=src client/src" tests/handlers/<file>
```
