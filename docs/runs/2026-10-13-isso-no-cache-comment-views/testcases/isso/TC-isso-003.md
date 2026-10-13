# TC-isso-003: A comment's author viewing that single comment gets a response no cache may store, in rendered and plain form

- area: isso
- tiles: isso.cache.single-comment-no-store
- role: comment author
- priority: high
- status: automated
- automated: isso/tests/test_no_cache_comment_views_api.py::TestNoCacheCommentViews::testViewWithEditCookieIsNoStoreWithAndWithoutPlain

## Preconditions

- The isso server is running with the spam guard switched off, so one client can post two comments in a row
- The same browser session makes every request, so it keeps the edit cookies the server sets when it posts

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /new?uri=/path/ with text "Hello *world*", author "Ada" and website "https://example.org/" | 201 Created; this becomes comment 1 and the browser now holds the edit cookie for comment 1 |
| 2 | POST /new?uri=/path/ with text "A reply" and parent 1 | 201 Created; this becomes comment 2 and the browser now holds the edit cookie for comment 2 |
| 3 | GET /id/1, sending the edit cookie for comment 1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
| 4 | GET /id/1?plain=1, sending the edit cookie for comment 1 | 200 OK; exactly one Cache-Control header, value exactly "no-store" |
