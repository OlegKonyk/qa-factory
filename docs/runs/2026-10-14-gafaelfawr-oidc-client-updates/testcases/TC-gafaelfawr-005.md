# TC-gafaelfawr-005: An update made with a second administrator's session cookie records that administrator and clears omitted notes

- area: gafaelfawr
- tiles: gafaelfawr.oidc-client-update.cookie-session-records-modifier
- role: administrator
- priority: medium
- status: automated
- automated: tests/handlers/test_oidc_client_updates_api.py::test_patch_by_other_admin_via_session_cookie

## Preconditions

- The OpenID Connect server is enabled in the deployment configuration
- Administrator admin-a has a token with the admin:oidc scope
- Administrator admin-b has a separate session with the admin:oidc scope, usable as a browser session cookie with its CSRF token
- Error alerts sent to the Slack channel are captured

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | admin-a registers a client with POST /auth/api/v1/oidc-clients, using their bearer token, return URI https://foo.example.com/service/, description "Original description" and notes "Notes to be cleared" | Response 201 with a Location header for the new client; last modified by is admin-a |
| 2 | Test setup sets the client's creation and last-modified times back to 2020-01-01 12:00:00 UTC in storage, then admin-a reads the client at its Location | Response 200; created and last modified both read 2020-01-01T12:00:00Z |
| 3 | Sign in as admin-b with a session cookie only (no bearer token from here on) and obtain the CSRF token for that session | The session cookie is set and a CSRF token is available |
| 4 | Note the current UTC time truncated to the whole second, then admin-b updates the client with PATCH at its Location, sending the session cookie and the X-CSRF-Token header, with return URI https://foo.example.com/other-service and description "Updated with a cookie" and no notes, then note the current UTC time again | Response 200; last modified by is admin-b; description reads "Updated with a cookie"; notes is present and empty (null); created is still 2020-01-01T12:00:00Z; last modified lies between the two noted times |
| 5 | Using only the session cookie, read the client at its Location | Response 200; last modified by is admin-b; return URI is https://foo.example.com/other-service; description reads "Updated with a cookie"; notes is left out of the response; created is 2020-01-01T12:00:00Z; last modified is the same value as in the step 4 response |
| 6 | Using only the session cookie, list all clients with GET /auth/api/v1/oidc-clients and find the client by its client ID | Response 200; the client appears exactly once and shows the same values as in step 5, with notes left out |
| 7 | Check the Slack alert channel | No error alerts were posted |
