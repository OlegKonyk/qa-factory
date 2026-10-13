# TC-isso-005: The comment listing and the single-comment view still return the same JSON content

- area: isso
- tiles: isso.cache.listing-and-view-bodies-unchanged
- role: comment author
- priority: high
- status: automated
- automated: isso/tests/test_no_cache_comment_views_api.py::TestNoCacheCommentViews::testListingAndViewBodiesAreUnchanged

## Preconditions

- The isso server is running with the spam guard switched off, so one client can post two comments in a row
- The same browser session makes every request, so it keeps the edit cookies the server sets when it posts

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | POST /new?uri=/path/ with text "Hello *world*", author "Ada" and website "https://example.org/" | 201 Created; this becomes comment 1 and the browser now holds its edit cookie |
| 2 | POST /new?uri=/path/ with text "A reply" and parent 1 | 201 Created; this becomes comment 2, a reply to comment 1 |
| 3 | GET /?uri=/path/ and look at the top level of the JSON | 200 OK; the body has id, total_replies, hidden_replies, replies and config; id is null, total_replies is 2, hidden_replies is 0, and replies holds exactly one comment |
| 4 | Look at that one top-level comment | It has id, parent, text, author, website, mode, total_replies, hidden_replies and replies; id is 1, parent is null, text is `<p>Hello <em>world</em></p>`, author is "Ada", website is "https://example.org/", mode is 1, total_replies is 1, hidden_replies is 0, and replies holds exactly one comment |
| 5 | Look at the reply nested under comment 1 | It has id, parent and text; id is 2, parent is 1, and text is `<p>A reply</p>` |
| 6 | GET /id/1, sending the edit cookie for comment 1 | 200 OK; the body has id, parent, text, author, website, mode, likes and dislikes; id is 1, parent is null, text is `<p>Hello <em>world</em></p>`, author is "Ada", website is "https://example.org/", mode is 1, likes is 0 and dislikes is 0 |
| 7 | GET /id/1?plain=1, sending the edit cookie for comment 1 | 200 OK; the body has text, and it is the raw "Hello *world*" as typed, not rendered |
