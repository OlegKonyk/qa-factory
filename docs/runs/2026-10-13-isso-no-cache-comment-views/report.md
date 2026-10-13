# isso-no-cache-comment-views: Stop browsers and proxies caching comment listings and single comments

QA mode: blind. Steps: frame pass; plan pass; implement pass; verify pass; review pass; ship pass.

## Tests

| file | test | kind | with the change | without the change | failure on the old code |
|---|---|---|---|---|---|
| isso/tests/test_no_cache_comment_views_api.py | TestNoCacheCommentViews::testErrorResponsesCarryNoCacheControl | API | pass | passes on the old code too: proves nothing | - |
| isso/tests/test_no_cache_comment_views_api.py | TestNoCacheCommentViews::testListingAndViewBodiesAreUnchanged | API | pass | passes on the old code too: proves nothing | - |
| isso/tests/test_no_cache_comment_views_api.py | TestNoCacheCommentViews::testListingOfThreadWithCommentIsNoStore | API | pass | fails on the old code: proves the change | Lists differ: [] != ['no-store'] |
| isso/tests/test_no_cache_comment_views_api.py | TestNoCacheCommentViews::testListingWithEachQueryParameterIsNoStore | API | pass | fails on the old code: proves the change | {'/?u[30 chars]00, []), '/?uri=%2Fpath%2F&sort=newest': (200,[503 chars] [])} != {'/?u[30 chars]00,  |
| isso/tests/test_no_cache_comment_views_api.py | TestNoCacheCommentViews::testOtherRoutesDoNotGetNoStore | API | pass | passes on the old code too: proves nothing | - |
| isso/tests/test_no_cache_comment_views_api.py | TestNoCacheCommentViews::testViewWithEditCookieIsNoStoreWithAndWithoutPlain | API | pass | fails on the old code: proves the change | {'/id/1': (200, []), '/id/1?plain=1': (200, [])} != {'/id/1': (200, ['no-store']), '/id/1?plain=1':  |

Counts (round 3):

| count | value |
|---|---|
| tests | 6 |
| tests_api | 6 |
| tests_browser | 0 |
| pass_at_head | 6 |
| fail_at_base_on_assertion | 3 |
| pass_on_both | 3 |
| missing_name | 0 |
| crash | 0 |
| head_fails | 0 |

## The developers' own tests, written with the change

0 of 2 new tests by the developers fail on the old code on an assertion; 2 fail only for a missing name

| file | test | with the change | without the change | failure on the old code |
|---|---|---|---|---|
| isso/tests/test_comments.py | TestComments::testFetchAddsNoCacheHeaders | pass | fails on the old code only for a name the change adds | cannot import name 'NO_CACHE_HEADERS' from 'isso.utils' (/Users/oleg/dev/qa-factory/.artifacts/runs/ |
| isso/tests/test_comments.py | TestComments::testViewAddsNoCacheHeaders | pass | fails on the old code only for a name the change adds | cannot import name 'NO_CACHE_HEADERS' from 'isso.utils' (/Users/oleg/dev/qa-factory/.artifacts/runs/ |

## Readable test cases

| case | title | link |
|---|---|---|
| isso/TC-isso-001.md | TC-isso-001: The comment listing of a thread that has comments tells every cache not to store it | [TC-isso-001.md](../../../.artifacts/runs/isso-no-cache-comment-views/verify/testcases/isso/TC-isso-001.md) |
| isso/TC-isso-002.md | TC-isso-002: The comment listing stays uncacheable with every query option, and for a thread with no comments | [TC-isso-002.md](../../../.artifacts/runs/isso-no-cache-comment-views/verify/testcases/isso/TC-isso-002.md) |
| isso/TC-isso-003.md | TC-isso-003: A comment's author viewing that single comment gets a response no cache may store, in rendered and plain form | [TC-isso-003.md](../../../.artifacts/runs/isso-no-cache-comment-views/verify/testcases/isso/TC-isso-003.md) |
| isso/TC-isso-004.md | TC-isso-004: Error responses from the comment listing and the single-comment view carry no Cache-Control header | [TC-isso-004.md](../../../.artifacts/runs/isso-no-cache-comment-views/verify/testcases/isso/TC-isso-004.md) |
| isso/TC-isso-005.md | TC-isso-005: The comment listing and the single-comment view still return the same JSON content | [TC-isso-005.md](../../../.artifacts/runs/isso-no-cache-comment-views/verify/testcases/isso/TC-isso-005.md) |
| isso/TC-isso-006.md | TC-isso-006: Posting, editing, counting, latest comments, config and deleting do not gain a Cache-Control header | [TC-isso-006.md](../../../.artifacts/runs/isso-no-cache-comment-views/verify/testcases/isso/TC-isso-006.md) |

## Mutation

| set | checked | killed | score | changed lines checked | killed | score |
|---|---|---|---|---|---|---|
| generated | 0 | 0 | - | 0 | 0 | - |

### Surviving mutants

#### generated: 0 survived


## Rounds

| round | kind | failure |
|---|---|---|
| 3 | write | - |

Stronger model's decisions: -

| ledger | value |
|---|---|
| caps | writer_rounds 3, advice 2, usd 10.0 |
| writer rounds used | 0 |
| stronger-model calls used | 0 |
| model calls in the ledger | 4 |
| spent (USD) | 5.3675 |

## Time and spend

| step | status | duration (s) | checks (s) | cost (USD) | model |
|---|---|---|---|---|---|
| frame | pass | 15.93 | - | 0.1537 | claude-sonnet-5-5 |
| plan | pass | 16.066 | - | 0.1714 | claude-sonnet-5-5 |
| implement | pass | 0.055 | - | - | - |
| verify | pass | 450.627 | 450.7 | 3.2233 | - |
| review | pass | 63.967 | - | 0.2679 | claude-opus-5-5 |
| ship | pass | 2.291 | - | - | - |

Total spend: 5.6925 USD (measured, from the run's records).
