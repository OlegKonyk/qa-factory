# TC-bookmarks-003: An unknown sort value in the bookmarks API falls back to newest added first

- area: bookmarks
- tiles: bookmarks.sort.unknown-value-falls-back-to-added-desc
- role: user
- priority: medium
- status: automated
- automated: bookmarks/tests/test_sort_by_modified_blind_api.py::SortByModifiedApiTestCase::test_list_bookmarks_unknown_sort_falls_back_to_added_desc

## Preconditions

- The user is authenticated against the REST API
- The user owns bookmark "Oldest added, middle modified" (added 30 days ago, modified 5 days ago)
- The user owns bookmark "Middle added, oldest modified" (added 20 days ago, modified 10 days ago)
- The user owns bookmark "Newest added, newest modified" (added 10 days ago, modified 1 day ago)
- The user also owns three archived bookmarks with the same titles and the same added and modified dates

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | Request GET /api/bookmarks/?sort=bogus | HTTP 200; exactly the three non-archived bookmarks, newest added first: "Newest added, newest modified", "Middle added, oldest modified", "Oldest added, middle modified" |
| 2 | Request GET /api/bookmarks/archived/?sort=bogus | HTTP 200; exactly the three archived bookmarks, newest added first: "Newest added, newest modified", "Middle added, oldest modified", "Oldest added, middle modified" |
