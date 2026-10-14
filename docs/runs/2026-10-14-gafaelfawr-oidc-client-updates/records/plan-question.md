# Step 2 plan needs a person

Kind: plan

Who: Oleg

Question: The test plan for 'Updating an OpenID Connect client does not record who changed it or when' needs a look before tests are written:
- not in the strategy: Regex check for no fractional seconds on timestamp strings: the strategy only says to compare with datetime.fromisoformat, so this is an invented assertion.
- not in the strategy: Creating two distinct admin users via create_session_token with different usernames in one test: inferred from the helper signature, not shown in the strategy.
- not in the strategy: Creating a client with a bearer token and patching it with a session cookie in one test: the strategy does not show mixing auth methods.

Accepted answers:

- `approve`: the plan stands as written
- `edit` (with "plan"): the edited plan replaces the plan: a path to a JSON file in the plan's structured shape, or to plan/plan.json itself edited in place, or the object inline; the file replaced is kept as plan.before-edit.json
- `decline`: the step fails with the note as its reason

Context:

```json
{
  "risk": "medium",
  "unknown_patterns": [
    "Regex check for no fractional seconds on timestamp strings: the strategy only says to compare with datetime.fromisoformat, so this is an invented assertion.",
    "Creating two distinct admin users via create_session_token with different usernames in one test: inferred from the helper signature, not shown in the strategy.",
    "Creating a client with a bearer token and patching it with a session cookie in one test: the strategy does not show mixing auth methods."
  ],
  "tests": [
    {
      "surface": "api",
      "file": "tests/handlers/test_oidc_client_updates_api.py",
      "name": "test_patch_by_other_admin_records_modifier",
      "covers": [
        "AC1",
        "AC2",
        "AC5"
      ],
      "reason": "Admin A (create_session_token, scope admin:oidc) POSTs a client and records created. Admin B, a different username with admin:oidc, PATCHes with new return_uri, description and notes. Asserts the PATCH response has last_modified_by == B's literal username. Then GETs the client and the list and asserts last_modified_by == B and the new return_uri, description and notes in both. Asserts created in both GETs equals the POST value. Fails today because last_modified_by stays A's."
    },
    {
      "surface": "api",
      "file": "tests/handlers/test_oidc_client_updates_api.py",
      "name": "test_patch_last_modified_not_before_send_time",
      "covers": [
        "AC3",
        "AC4"
      ],
      "reason": "Takes before = datetime.now(tz=UTC).replace(microsecond=0) in the test, then PATCHes. Parses last_modified and created with datetime.fromisoformat from the POST, PATCH and both GET responses. Asserts last_modified >= before and last_modified >= created. Asserts every timestamp string matches ^\\d{4}-\\d\\d-\\d\\dT\\d\\d:\\d\\d:\\d\\dZ$ (no fraction). Uses no sleep. The before bound fails today because last_modified still holds the creation time, but only when the PATCH falls in a later second than the POST. The test therefore also compares against the second-truncated send time rather than relying on created alone. This is the strongest check available without a sleep."
    },
    {
      "surface": "api",
      "file": "tests/handlers/test_oidc_client_updates_api.py",
      "name": "test_patch_by_creator_keeps_creator_as_modifier",
      "covers": [
        "AC6",
        "AC4"
      ],
      "reason": "The creator PATCHes their own client. Asserts last_modified_by == the creator's username in the PATCH response and in a GET. Asserts that last_modified >= created. This guards against an implementation that writes the wrong user or blanks the field. It already passes today, so it is a regression guard."
    },
    {
      "surface": "api",
      "file": "tests/handlers/test_oidc_client_updates_api.py",
      "name": "test_patch_by_other_admin_via_session_cookie",
      "covers": [
        "AC1",
        "AC2"
      ],
      "reason": "Admin A creates the client with a bearer token. Admin B patches through set_session_cookie with an X-CSRF-Token header. Asserts last_modified_by == B's username in the PATCH response and in a GET. The contract allows both auth routes, and the cookie path resolves the caller differently from the bearer path, so a change that only handles token auth would otherwise pass."
    }
  ],
  "placement_reason": "The strategy puts all coverage at the API level in a new tests/handlers/test_<feature>_api.py file, and gafaelfawr has no browser tests. So all four tests go in the new file tests/handlers/test_oidc_client_updates_api.py. They use the client and factory fixtures, create_session_token from ..support.tokens, and set_session_cookie from ..support.cookies. They use the config \"github-oidc-server\", which the existing tests of the same routes in tests/handlers/api_oidc_test.py use. All results are read back through GET routes, with literal expected values and timestamps compared via datetime.fromisoformat. I saw no developer tests, so every criterion is covered here. I read only the existing test parametrization and not the route code, so the cookie-path username behaviour is inferred from the ticket.",
  "plan": "/Users/oleg/dev/qa-factory/.artifacts/runs/gafaelfawr-oidc-client-updates/plan/plan.json"
}
```

Answer by writing /Users/oleg/dev/qa-factory/.artifacts/runs/gafaelfawr-oidc-client-updates/answer.json (`by` is required), for example:

```json
{"decision": "approve", "by": "Oleg", "note": ""}
```
