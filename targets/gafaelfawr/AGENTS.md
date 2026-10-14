# Agent notes for gafaelfawr (written by the qa-factory onboarding, not upstream)

gafaelfawr is a FastAPI authentication and authorization service. Python 3.14, uv. Two packages:
the server under `src/gafaelfawr` and the client `rubin.gafaelfawr` under `client/src` (installed
editable by the `dev` group; it has its own noxfile and tests under `client/`).

## Environment

    uv sync --frozen --inexact --python 3.14     # dev group: pytest, testcontainers, the client
    uv pip install --python .venv/bin/python ruff mutmut==3.8.0

## Tests

The suite starts Postgres 18 and Redis 8 itself through testcontainers (session-scoped fixtures in
`tests/conftest.py`), so Docker must be running. Some tests run the `alembic` console script, so the
environment's `bin` folder must be on PATH. On a Mac with Colima, also set
`TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock`.

The suite's database fixture (`empty_database` in `tests/conftest.py`) stamps the schema with
`alembic.ini` and the `alembic/` folder at the repository root (found as `Path(__file__).parent.parent`),
so any copy of the tree that runs the tests (mutmut's `mutants/`, for one) needs both.

    PATH=$PWD/.venv/bin:$PATH .venv/bin/python -m pytest -p no:cacheprovider tests
    PATH=$PWD/.venv/bin:$PATH .venv/bin/python -m pytest -p no:cacheprovider tests/handlers/api_oidc_test.py

From a git worktree of this clone add `-o "pythonpath=src client/src"` so the worktree's code is
imported, not the clone's (the editable installs point at the clone).

- Test files are `*_test.py`, laid out like `src/gafaelfawr` (handlers, services, storage...).
- `tests` is a package: imports between test modules are relative (`from ..support.tokens import
  create_session_token`).
- HTTP tests use the `client` fixture (an httpx `AsyncClient` on the app), `factory` for setup, and
  `@pytest.mark.parametrize("config", ["<name>"], indirect=True)` to pick a config from
  `tests/data/config/`. Async tests carry `@pytest.mark.asyncio` (strict mode).
- Helpers live in `tests/support/` (tokens, cookies, constants, headers, ...).

## Lint

    .venv/bin/python -m ruff check . && .venv/bin/python -m ruff format --check .

The project's own lint, typing and test sessions are in `noxfile.py` (`uv run --only-group=nox nox
-s lint typing test`), which CI runs.

## API description

FastAPI serves OpenAPI at `/auth/openapi.json` (docs at `/auth/docs`).
