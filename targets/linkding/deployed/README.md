# linkding sort-by-modified, against a deployed instance

The four readable cases of the shipped run
(`docs/runs/2026-10-10-linkding-sort-by-modified-blind/testcases/TC-bookmarks-001.md` to `004.md`)
ported to run against a running linkding, with every bookmark created through the public REST API.
The in-suite versions sit beside the cases under `tests/`; they need linkding's own source tree,
its ORM and Django's test client.

## Start an instance

Docker (here through colima). Release 1.46.0 is the first that contains the sort-by-modified
feature; 1.47.0 is the one this suite was run against.

```
docker run -d --name qa-factory-linkding -p 9090:9090 \
  -e LD_SUPERUSER_NAME=qa -e LD_SUPERUSER_PASSWORD=<password> sissbruecker/linkding:1.47.0
until curl -fsS http://127.0.0.1:9090/health; do sleep 0.2; done
```

The API token is environment setup, not test data: it is read once per instance, the way a test
account's credentials would be handed to a suite in a shared environment. linkding 1.47.0
authenticates against its own `bookmarks.models.ApiToken`, not Django REST framework's `Token`:

```
docker exec qa-factory-linkding python manage.py shell -c "from django.contrib.auth.models import User; from bookmarks.models import ApiToken; print(ApiToken.objects.get_or_create(user=User.objects.get(username='qa'), name='qa-factory')[0].key)" 2>/dev/null | tail -1
```

Remove it afterwards: `docker rm -f qa-factory-linkding`.

## Environment

| variable | used by | default |
|---|---|---|
| `LINKDING_URL` | all cases | `http://127.0.0.1:9090` |
| `LINKDING_TOKEN` | all cases (data setup) | none: the cases skip |
| `LINKDING_USER`, `LINKDING_PASSWORD` | 004, the browser case | none: 004 skips |

## Run

Once: `uv sync --group deployed && uv run --no-sync playwright install chromium`. Then:

```
LINKDING_TOKEN=<token> LINKDING_USER=qa LINKDING_PASSWORD=<password> \
  uv run --no-sync pytest targets/linkding/deployed --durations=0
```

The root `uv run pytest` does not collect this folder (`testpaths = ["tests"]`).

| case | test | result on 1.47.0 (2026-10-14) |
|---|---|---|
| TC-bookmarks-001 | `test_list_bookmarks_sort_modified_asc_and_desc` | passed |
| TC-bookmarks-002 | `test_list_archived_bookmarks_sort_modified_asc_and_desc` | passed |
| TC-bookmarks-003 | `test_list_bookmarks_unknown_sort_falls_back_to_added_desc` | passed |
| TC-bookmarks-004 | `test_sort_dropdown_modified_options_reorder_list[chromium]` | passed |

Wall time about 3 s for the four, against a local container that starts in about 3 s.

## What had to change from the in-suite tests, and why

- **Modified order through edits.** The in-suite tests set `date_modified` on the model; the API
  cannot. Each test edits the bookmarks (`PATCH` of the description) in the order the case needs
  and reads `date_modified` back, requiring it to be later than the previous edit's before going
  on. Measured on 1.47.0: every `PATCH` moves it, at microsecond resolution, about 8 ms per edit.
- **Added order through creation order.** `date_added` cannot be set either; the bookmarks are
  created oldest-added first. The cases' days-ago dates become milliseconds apart; the order is
  what the cases check, so they are unchanged.
- **Scoped by a marker.** Every title and URL carries a marker unique to the test, and every list
  request (API `q=`, browser `?q=`) searches for it, so "exactly three" holds on an instance with
  other data and with leftovers of an earlier run. URLs carry it too because linkding treats a
  `POST` of an existing URL as an update of that bookmark.
- **Cleanup through the API.** Each test deletes what it created, in a `finally`, also when it fails.
- **No other user in 001.** The in-suite test adds another user's bookmark to show it is left out.
  With one token the suite cannot create a second user or act as one; creating one through
  `manage.py` would make test data depend on shell access to the container. The precondition is
  dropped; isolation between users is left to the in-suite test.
- **Ids, not titles, in the API checks**, as the in-suite tests do, read from the create responses.
- **Login through the form instead of a logged-in test client** (004): the user and password come
  from the environment.
- **Locators by role** (004): the in-suite test used `ul.bookmark-list > li` and
  `select[name="sort"]`. The bookmark list is the first list in the "Bookmark list" region (the
  region also holds the pagination list). The sort selector is the page's one combobox, not
  `get_by_label("Sort by")`: after a sort is applied, linkding 1.47.0 gives the search form's
  hidden `sort` input the same id as the select (`id_sort`), so the label points at the hidden
  input. That is a defect in linkding's markup, found by this run.
