# TC-bookmarks-004: API falls back to newest-added-first order when the sort value is unknown

- area: bookmarks
- tiles: bookmarks.sort.unknown-value-falls-back-to-default
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_bookmarks_unknown_sort_falls_back_to_default_order

## Preconditions

- The user is authenticated to the REST API with their API token
- The user has three unarchived bookmarks (dates in UTC): A added 2020-01-01 and modified 2022-01-01, B added 2021-01-01 and modified 2020-01-01, C added 2022-01-01 and modified 2021-01-01

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Request `GET /api/bookmarks/?sort=bogus` | The response status is 200 and the results list exactly C, B, A in that order (added 2022-01-01, 2021-01-01, 2020-01-01), the default newest-added-first order |
