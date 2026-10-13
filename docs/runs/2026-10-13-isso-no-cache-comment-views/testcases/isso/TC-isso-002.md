# TC-isso-002: The comment listing stays uncacheable with every query option, and for a thread with no comments

- area: isso
- tiles: isso.cache.thread-listing-no-store-any-query
- role: reader
- priority: medium
- status: automated
- automated: isso/tests/test_no_cache_comment_views_api.py::TestNoCacheCommentViews::testListingWithEachQueryParameterIsNoStore

## Preconditions

- The isso server is running with the spam guard switched off, so one client can post two comments in a row

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /new?uri=/path/ with text "Hello *world*", author "Ada" and website "https://example.org/" | 201 Created; this becomes comment 1 |
| 2 | POST /new?uri=/path/ with text "A reply" and parent 1 | 201 Created; this becomes comment 2, a reply to comment 1 |
| 3 | GET /?uri=/path/&sort=oldest | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 4 | GET /?uri=/path/&sort=newest | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 5 | GET /?uri=/path/&sort=upvotes | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 6 | GET /?uri=/path/&limit=1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 7 | GET /?uri=/path/&limit=0 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 8 | GET /?uri=/path/&limit=1&offset=1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 9 | GET /?uri=/path/&parent=1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 10 | GET /?uri=/path/&nested_limit=0 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 11 | GET /?uri=/path/&nested_limit=1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 12 | GET /?uri=/path/&plain=1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 13 | GET /?uri=/path/&after=0 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 14 | GET /?uri=/path/&sort=newest&limit=1&offset=0&nested_limit=1&plain=1&after=0 (all options at once) | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 15 | GET /?uri=/empty/ (a thread nobody has commented on) | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
