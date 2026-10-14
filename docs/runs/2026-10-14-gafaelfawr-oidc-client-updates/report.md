# gafaelfawr-oidc-client-updates: Updating an OpenID Connect client does not record who changed it or when

QA mode: blind. Steps: frame pass; plan pass; implement pass; verify pass; review pass; ship pass.

## Tests

| file | test | kind | with the change | without the change | failure on the old code |
|---|---|---|---|---|---|
| tests/handlers/test_oidc_client_updates_api.py | test_patch_by_other_admin_records_modifier[github-oidc-server] | API | pass | fails on the old code: proves the change | assert 'admin-a' == 'admin-b' |
| tests/handlers/test_oidc_client_updates_api.py | test_patch_last_modified_is_time_of_update[github-oidc-server] | API | pass | fails on the old code: proves the change | assert datetime.datetime(2026, 10, 14, 16, 37, 19, tzinfo=datetime.timezone.utc) <= datetime.datetim |
| tests/handlers/test_oidc_client_updates_api.py | test_timestamps_in_whole_seconds[github-oidc-server] | API | pass | fails on the old code: proves the change | created is not in whole seconds: 2026-10-14T16:37:19.864817Z |
| tests/handlers/test_oidc_client_updates_api.py | test_patch_by_creator_keeps_creator_as_modifier[github-oidc-server] | API | pass | fails on the old code: proves the change | assert datetime.datetime(2026, 10, 14, 16, 37, 20, tzinfo=datetime.timezone.utc) <= datetime.datetim |
| tests/handlers/test_oidc_client_updates_api.py | test_patch_by_other_admin_via_session_cookie[github-oidc-server] | API | pass | fails on the old code: proves the change | assert 'admin-a' == 'admin-b' |
| tests/handlers/test_oidc_client_updates_api.py | test_refused_patch_leaves_client_unchanged[github-oidc-server] | API | pass | passes on the old code too: proves nothing | - |

Counts (round 4):

| count | value |
|---|---|
| tests | 6 |
| tests_api | 6 |
| tests_browser | 0 |
| pass_at_head | 6 |
| fail_at_base_on_assertion | 5 |
| pass_on_both | 1 |
| missing_name | 0 |
| crash | 0 |
| head_fails | 0 |

## The developers' own tests, written with the change

1 of 1 tests by the developers (0 new, 1 modified) fail on the old code on an assertion; 0 fail only for a missing name

| file | test | kind | with the change | without the change | failure on the old code |
|---|---|---|---|---|---|
| tests/handlers/api_oidc_test.py | test_lifecycle | modified | pass | fails on the old code: proves the change | assert {'return_uri'...ple.com', ...} == {'client_id':...ewlines', ...} |

## Readable test cases

| case | title | link |
|---|---|---|
| gafaelfawr/TC-gafaelfawr-001.md | TC-gafaelfawr-001: An update by a second administrator records that administrator as the last modifier | [TC-gafaelfawr-001.md](verify/testcases/gafaelfawr/TC-gafaelfawr-001.md) |
| gafaelfawr/TC-gafaelfawr-002.md | TC-gafaelfawr-002: An update sets the last-modified time to the moment of the update and leaves the creation time alone | [TC-gafaelfawr-002.md](verify/testcases/gafaelfawr/TC-gafaelfawr-002.md) |
| gafaelfawr/TC-gafaelfawr-003.md | TC-gafaelfawr-003: Creation and last-modified times are shown in whole UTC seconds on create, update, read and list | [TC-gafaelfawr-003.md](verify/testcases/gafaelfawr/TC-gafaelfawr-003.md) |
| gafaelfawr/TC-gafaelfawr-004.md | TC-gafaelfawr-004: An update by the creator keeps the creator as last modifier and moves the last-modified time | [TC-gafaelfawr-004.md](verify/testcases/gafaelfawr/TC-gafaelfawr-004.md) |
| gafaelfawr/TC-gafaelfawr-005.md | TC-gafaelfawr-005: An update made with a second administrator's session cookie records that administrator and clears omitted notes | [TC-gafaelfawr-005.md](verify/testcases/gafaelfawr/TC-gafaelfawr-005.md) |
| gafaelfawr/TC-gafaelfawr-006.md | TC-gafaelfawr-006: Refused updates leave the client and its audit fields unchanged | [TC-gafaelfawr-006.md](verify/testcases/gafaelfawr/TC-gafaelfawr-006.md) |

## Mutation

| set | checked | killed | score | changed lines checked | killed | score |
|---|---|---|---|---|---|---|
| generated | 71 | 64 | 0.9014 | 24 | 24 | 1.0 |
| generated_and_developers | 71 | 65 | 0.9155 | 24 | 24 | 1.0 |
| developers | 71 | 63 | 0.8873 | 24 | 22 | 0.9167 |

### Surviving mutants

#### generated: 7 survived

| mutant | source line | on a changed line |
|---|---|---|
| gafaelfawr.services.oidc.xǁOIDCServiceǁupdate_client__mutmut_10 | 528 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_16 | 255 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_24 | 255 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_40 | 264 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_41 | 265 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_42 | 265 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_43 | 265 | no |

#### generated_and_developers: 6 survived

| mutant | source line | on a changed line |
|---|---|---|
| gafaelfawr.services.oidc.xǁOIDCServiceǁupdate_client__mutmut_10 | 528 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_16 | 255 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_24 | 255 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_41 | 265 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_42 | 265 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_43 | 265 | no |

#### developers: 8 survived

| mutant | source line | on a changed line |
|---|---|---|
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_10 | 249 | **changed line** |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁupdate__mutmut_4 | 293 | **changed line** |
| gafaelfawr.services.oidc.xǁOIDCServiceǁupdate_client__mutmut_10 | 528 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_16 | 255 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_24 | 255 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_41 | 265 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_42 | 265 | no |
| gafaelfawr.storage.oidc.xǁOIDCClientStoreǁregister__mutmut_43 | 265 | no |

## Rounds

| round | kind | failure |
|---|---|---|
| 3 | write | - |
| 4 | review_fix | - |
| 4 | resume | - |

Stronger model's decisions: -

| ledger | value |
|---|---|
| caps | writer_rounds 3, advice 2, usd 12.0 |
| writer rounds used | 1 |
| stronger-model calls used | 0 |
| model calls in the ledger | 9 |
| spent (USD) | 9.2098 |

## Who answered

| step | round | by | decision | note | answered at |
|---|---|---|---|---|---|
| plan | 2 | the onboarding agent | approve | All three patterns are in the application's own tests at base: tests/handlers/api_oidc_test.py test_unauthorized makes two tokens with create_session_token, test_auth_required creates a client through a session cookie; the no-fraction check is contract line 5 (whole-second timestamps), checked on both commits by a probe. Answered by the onboarding agent under the brief's instruction to answer gates itself. | 2026-10-14T15:47:31+00:00 |

## Time and spend

| step | status | duration (s) | checks (s) | cost (USD) | model |
|---|---|---|---|---|---|
| frame | pass | 11.232 | - | 0.0379 | claude-sonnet-5-5 |
| plan | pass | 0.0 | - | - | - |
| implement | pass | 0.041 | - | - | - |
| verify | pass | 718.381 | 718.4 | 2.7274 | - |
| review | pass | 65.573 | - | 0.2307 | claude-opus-5-5 |
| ship | pass | 59.186 | - | - | - |

Total spend: 9.2477 USD (measured, from the run's records).
