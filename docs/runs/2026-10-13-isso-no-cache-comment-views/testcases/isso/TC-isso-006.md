# TC-isso-006: Posting, editing, counting, latest comments, config and deleting do not gain a Cache-Control header

- area: isso
- tiles: isso.cache.other-routes-unchanged
- role: comment author
- priority: medium
- status: automated
- automated: isso/tests/test_no_cache_comment_views_api.py::TestNoCacheCommentViews::testOtherRoutesDoNotGetNoStore

## Preconditions

- The isso server is running with the spam guard switched off
- The "latest comments" feature is enabled in the server configuration
- The same browser session makes every request, so it keeps the edit cookie the server sets when it posts

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /new?uri=/path/ with text "Lorem ipsum ..." | 201 Created; this becomes comment 1; the response has no Cache-Control header at all |
| 2 | PUT /id/1 with text "Edited", sending the edit cookie for comment 1 | 200 OK; the response has no Cache-Control header at all |
| 3 | POST /count with the list of threads ["/path/"] | 200 OK; the response has no Cache-Control header at all |
| 4 | GET /latest?limit=5 | 200 OK; the response has no Cache-Control header at all |
| 5 | GET /config | 200 OK; the response has no Cache-Control header at all |
| 6 | DELETE /id/1, sending the edit cookie for comment 1 (done last, because deleting clears the edit cookie) | 200 OK; the response has no Cache-Control header at all |
