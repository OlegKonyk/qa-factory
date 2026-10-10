# TC-bookmarks-001: The bookmarks API sorts a user's bookmarks by modification date, ascending and descending

- area: bookmarks
- tiles: bookmarks.sort.modified-asc-and-desc-api
- role: user
- priority: high
- status: automated
- automated: bookmarks/tests/test_sort_by_modified_blind_api.py::SortByModifiedApiTestCase::test_list_bookmarks_sort_modified_asc_and_desc

## Preconditions

- The user is authenticated against the REST API
- The user owns bookmark "Oldest added, middle modified" (added 30 days ago, modified 5 days ago)
- The user owns bookmark "Middle added, oldest modified" (added 20 days ago, modified 10 days ago)
- The user owns bookmark "Newest added, newest modified" (added 10 days ago, modified 1 day ago)
- A different user owns one bookmark (added 15 days ago, modified 7 days ago)

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Request GET /api/bookmarks/?sort=modified_asc | HTTP 200; exactly three results, in this order: "Middle added, oldest modified", "Oldest added, middle modified", "Newest added, newest modified"; the other user's bookmark does not appear |
| 2 | Request GET /api/bookmarks/?sort=modified_desc | HTTP 200; exactly three results, in this order: "Newest added, newest modified", "Oldest added, middle modified", "Middle added, oldest modified"; the other user's bookmark does not appear |
