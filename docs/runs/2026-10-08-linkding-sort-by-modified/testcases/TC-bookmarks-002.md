# TC-bookmarks-002: API lists bookmarks most recently modified first when sorted by modified descending

- area: bookmarks
- tiles: bookmarks.sort.modified-descending
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_bookmarks_sort_modified_desc

## Preconditions

- The user is authenticated to the REST API with their API token
- The user has three unarchived bookmarks (dates in UTC): A added 2020-01-01 and modified 2022-01-01, B added 2021-01-01 and modified 2020-01-01, C added 2022-01-01 and modified 2021-01-01

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Request `GET /api/bookmarks/?sort=modified_desc` | The results list exactly A, C, B in that order (modified 2022-01-01, 2021-01-01, 2020-01-01), not the default newest-added order C, B, A |
