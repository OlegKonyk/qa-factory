# TC-bookmarks-003: Archived bookmarks API sorts by modified date in both directions and leaves out unarchived bookmarks

- area: bookmarks
- tiles: bookmarks.sort.archived-modified-order
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests/test_sort_by_modified_api.py::SortByModifiedApiTestCase::test_list_archived_bookmarks_sort_modified_asc_and_desc

## Preconditions

- The user is authenticated to the REST API with their API token
- The user has three archived bookmarks (dates in UTC): A added 2020-01-01 and modified 2022-01-01, B added 2021-01-01 and modified 2020-01-01, C added 2022-01-01 and modified 2021-01-01
- The user also has one unarchived bookmark D, added 2023-01-01 and modified 2021-06-01, which falls between the archived ones by modified date

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Request `GET /api/bookmarks/archived/?sort=modified_asc` | The results list exactly B, C, A in that order; the unarchived bookmark D does not appear |
| 2 | Request `GET /api/bookmarks/archived/?sort=modified_desc` | The results list exactly A, C, B in that order; the unarchived bookmark D does not appear |
