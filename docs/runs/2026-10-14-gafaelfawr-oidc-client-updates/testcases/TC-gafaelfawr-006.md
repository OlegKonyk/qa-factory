# TC-gafaelfawr-006: Refused updates leave the client and its audit fields unchanged

- area: gafaelfawr
- tiles: gafaelfawr.oidc-client-update.refused-update-changes-nothing
- role: administrator
- priority: medium
- status: automated
- automated: tests/handlers/test_oidc_client_updates_api.py::test_refused_patch_leaves_client_unchanged

## Preconditions

- The OpenID Connect server is enabled in the deployment configuration
- Administrator admin-a has a token with the admin:oidc scope
- Administrator admin-b has a separate token with the admin:oidc scope, also usable as a session cookie
- User some-user has a token with only the user:token scope, without admin:oidc
- Error alerts sent to the Slack channel are captured

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | admin-a registers a client with POST /auth/api/v1/oidc-clients, using their bearer token, return URI https://foo.example.com/service/ and description "Original description" | Response 201 with a Location header for the new client |
| 2 | Test setup sets the client's creation and last-modified times back to 2020-01-01 12:00:00 UTC in storage, then admin-a reads the client at its Location and keeps the full response as the reference | Response 200; created and last modified both read 2020-01-01T12:00:00Z; last modified by is admin-a |
| 3 | Send PATCH to the client's Location with no credentials, with return URI https://foo.example.com/other-service, description "Updated description" and notes "Should never be stored" | Response 401 |
| 4 | Send the same PATCH with some-user's bearer token | Response 403 |
| 5 | Send PATCH with admin-b's bearer token and a body containing only return URI https://foo.example.com/other-service (no description) | Response 422 |
| 6 | Send PATCH with admin-b's bearer token and a body containing only description "Updated description" (no return URI) | Response 422 |
| 7 | Send the full PATCH from step 3 with admin-b's bearer token to /auth/api/v1/oidc-clients/unknown-client.clients.example.com | Response 404 |
| 8 | Sign in as admin-b with a session cookie and send the full PATCH from step 3 to the client's Location without the X-CSRF-Token header, then sign out the cookie | Response 403 |
| 9 | admin-a reads the client at its Location | Response 200; the response is identical to the reference from step 2: return URI https://foo.example.com/service/, description "Original description", no notes, last modified by admin-a, created and last modified both 2020-01-01T12:00:00Z |
| 10 | Check the Slack alert channel | No error alerts were posted |
