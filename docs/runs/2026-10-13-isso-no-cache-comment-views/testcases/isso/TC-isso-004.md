# TC-isso-004: Error responses from the comment listing and the single-comment view carry no Cache-Control header

- area: isso
- tiles: isso.cache.error-responses-no-cache-control
- role: reader
- priority: high
- status: automated
- automated: isso/tests/test_no_cache_comment_views_api.py::TestNoCacheCommentViews::testErrorResponsesCarryNoCacheControl

## Preconditions

- The isso server is running with the spam guard switched off, so one client can post two comments in a row

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | In browser A, POST /new?uri=/path/ with text "Hello *world*", author "Ada" and website "https://example.org/" | 201 Created; this becomes comment 1 and browser A holds its edit cookie |
| 2 | In browser A, POST /new?uri=/path/ with text "A reply" and parent 1 | 201 Created; this becomes comment 2 |
| 3 | In browser A, GET /?uri=/path/&sort=bogus | 400 Bad Request; the response has no Cache-Control header at all |
| 4 | In browser A, GET /id/99 (no such comment exists) | 404 Not Found; the response has no Cache-Control header at all |
| 5 | In a fresh browser B that has never posted and holds no edit cookie, GET /id/1 | 403 Forbidden; the response has no Cache-Control header at all |
