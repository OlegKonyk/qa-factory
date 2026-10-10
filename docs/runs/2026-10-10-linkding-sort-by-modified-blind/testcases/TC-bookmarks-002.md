# TC-bookmarks-002: The archived bookmarks API sorts archived bookmarks by modification date, ascending and descending

- area: bookmarks
- tiles: bookmarks.sort.modified-asc-and-desc-archived-api
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests/test_sort_by_modified_blind_api.py::SortByModifiedApiTestCase::test_list_archived_bookmarks_sort_modified_asc_and_desc

## Preconditions

- The user is authenticated against the REST API
- The user owns archived bookmark "Oldest added, middle modified" (added 30 days ago, modified 5 days ago)
- The user owns archived bookmark "Middle added, oldest modified" (added 20 days ago, modified 10 days ago)
- The user owns archived bookmark "Newest added, newest modified" (added 10 days ago, modified 1 day ago)
- The user also owns one non-archived bookmark (added 15 days ago, modified 7 days ago)

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Request GET /api/bookmarks/archived/?sort=modified_asc | HTTP 200; exactly three results, in this order: "Middle added, oldest modified", "Oldest added, middle modified", "Newest added, newest modified"; the non-archived bookmark does not appear |
| 2 | Request GET /api/bookmarks/archived/?sort=modified_desc | HTTP 200; exactly three results, in this order: "Newest added, newest modified", "Oldest added, middle modified", "Middle added, oldest modified"; the non-archived bookmark does not appear |
