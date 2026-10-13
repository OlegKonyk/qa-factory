# TC-isso-001: The comment listing of a thread that has comments tells every cache not to store it

- area: isso
- tiles: isso.cache.thread-listing-no-store
- role: reader
- priority: high
- status: automated
- automated: isso/tests/test_no_cache_comment_views_api.py::TestNoCacheCommentViews::testListingOfThreadWithCommentIsNoStore

## Preconditions

- The isso server is running with the spam guard switched off, so one client can post two comments in a row

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /new?uri=/path/ with text "Hello *world*", author "Ada" and website "https://example.org/" | 201 Created; this becomes comment 1 |
| 2 | POST /new?uri=/path/ with text "A reply" and parent 1 | 201 Created; this becomes comment 2, a reply to comment 1 |
| 3 | GET /?uri=/path/ | 200 OK; the response has exactly one Cache-Control header and its value is exactly "no-store" |
