# Test strategy for linkding

linkding is a Django application with a REST API (Django REST framework) and server-rendered pages
that have Playwright browser tests. This file is the rule the test writer follows.

## Where new tests go

- **API level, most of the coverage.** `bookmarks/tests/test_<feature>_api.py`, using
  `LinkdingApiTestCase` and `BookmarkFactoryMixin` from `bookmarks/tests/helpers.py`.
  Reason: API tests are fast, deterministic and see the behaviour directly.
- **Browser level, one or two tests per feature.** `bookmarks/tests_e2e/e2e_test_<feature>.py`, using
  `LinkdingE2ETestCase` from `bookmarks/tests_e2e/helpers.py`. Cover only the path a user sees.
  Reason: browser tests are slow, so they protect the user-visible path and nothing more.
- **Unit tests belong to the implementer.** The test writer does not add them.
- Every placement decision is written down with its reason.

## How tests are written

- The application's conventions win over generic pytest style: unittest-style classes, the helpers'
  `setup_bookmark` and friends, and `self.client`.
- Tests use the public surface: query-string parameters, API JSON, visible controls. They never use
  the code's constants.
- Fixtures must make the new behaviour observable. For a sort, the order by the new key must differ
  from the default order.
- A test must fail on the code before the change, and for a behavioural reason, not a missing name.
- No sleeps. No mocking of the application's own code.

## Running the suite

Use the repository's virtual environment:

```
python -m pytest -p no:cacheprovider -n auto bookmarks/tests
python -m pytest -p no:cacheprovider -o python_files=e2e_test_*.py bookmarks/tests_e2e/<file>
```
