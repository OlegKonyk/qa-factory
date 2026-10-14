"""Tests for the audit fields of updated OpenID Connect clients."""

import re
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from safir.testing.slack import MockSlackWebhook
from sqlalchemy import text

from gafaelfawr.factory import Factory

from ..support.cookies import clear_session_cookie, set_session_cookie
from ..support.tokens import create_session_token

WHOLE_SECOND_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
"""UTC timestamp in whole seconds, without a fractional part."""

PAST = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
"""Creation time given to clients so that an update is observable."""


def assert_whole_seconds(client_json: dict[str, Any], field: str) -> None:
    """Check that a timestamp field is in UTC with no fractional seconds."""
    assert field in client_json
    assert WHOLE_SECOND_TIMESTAMP.match(client_json[field]), (
        f"{field} is not in whole seconds: {client_json[field]}"
    )


def find_client(
    clients: list[dict[str, Any]], client_id: str
) -> dict[str, Any]:
    """Find a client by ID in the client list."""
    matches = [c for c in clients if c.get("client_id") == client_id]
    assert len(matches) == 1, f"{client_id} not found in {clients}"
    return matches[0]


async def backdate_client(
    client: AsyncClient,
    factory: Factory,
    client_url: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    """Move the creation and modification time of a client into the past.

    POST and PATCH in a test usually run in the same second, so without this
    an update that kept the creation time would be indistinguishable from one
    that recorded the time of the update. The database is only changed here
    as setup; the result is read back through the API.
    """
    client_id = client_url.rsplit("/", 1)[-1]
    async with factory.session.begin():
        await factory.session.execute(
            text(
                "UPDATE oidc_client SET created = :when, last_modified = :when"
                " WHERE client_id = :client_id"
            ),
            {"when": PAST.replace(tzinfo=None), "client_id": client_id},
        )
    r = await client.get(client_url, headers=headers)
    assert r.status_code == 200
    client_json = r.json()
    assert client_json["created"] == "2020-01-01T12:00:00Z"
    assert client_json["last_modified"] == "2020-01-01T12:00:00Z"
    return client_json


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_by_other_admin_records_modifier(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}
    headers_b = {"Authorization": f"Bearer {admin_b.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Original description",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    created_json = r.json()
    assert created_json["last_modified_by"] == "admin-a"
    client_id = created_json["client_id"]
    client_url = r.headers["Location"]
    await backdate_client(client, factory, client_url, headers_a)

    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
            "notes": "Updated by a second administrator",
        },
        headers=headers_b,
    )
    assert r.status_code == 200
    patch_json = r.json()
    assert "last_modified_by" in patch_json
    assert patch_json["last_modified_by"] == "admin-b"
    assert patch_json["return_uri"] == "https://foo.example.com/other-service"
    assert patch_json["description"] == "Updated description"
    assert patch_json["notes"] == "Updated by a second administrator"
    assert patch_json["created"] == "2020-01-01T12:00:00Z"
    assert "last_modified" in patch_json
    assert patch_json["last_modified"] != "2020-01-01T12:00:00Z"
    assert "client_secret" not in patch_json

    # Both retrieval routes, whichever administrator calls them, show the
    # updated client with the same audit fields as the PATCH response.
    r = await client.get(client_url, headers=headers_a)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients", headers=headers_a)
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert "last_modified_by" in seen
        assert seen["last_modified_by"] == "admin-b"
        assert seen["return_uri"] == "https://foo.example.com/other-service"
        assert seen["description"] == "Updated description"
        assert seen["notes"] == "Updated by a second administrator"
        assert seen["created"] == "2020-01-01T12:00:00Z"
        assert "last_modified" in seen
        assert seen["last_modified"] == patch_json["last_modified"]

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_last_modified_is_time_of_update(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}
    headers_b = {"Authorization": f"Bearer {admin_b.token}"}

    start = datetime.now(tz=UTC).replace(microsecond=0)
    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Test client",
        },
        headers=headers_a,
    )
    end = datetime.now(tz=UTC)
    assert r.status_code == 201
    post_json = r.json()
    assert post_json["last_modified"] == post_json["created"]
    assert start <= datetime.fromisoformat(post_json["created"]) <= end
    client_id = post_json["client_id"]
    client_url = r.headers["Location"]
    await backdate_client(client, factory, client_url, headers_a)

    before = datetime.now(tz=UTC).replace(microsecond=0)
    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
        },
        headers=headers_b,
    )
    after = datetime.now(tz=UTC)
    assert r.status_code == 200
    patch_json = r.json()
    assert datetime.fromisoformat(patch_json["created"]) == PAST
    last_modified = datetime.fromisoformat(patch_json["last_modified"])
    assert before <= last_modified <= after
    assert last_modified > PAST

    r = await client.get(client_url, headers=headers_b)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients", headers=headers_b)
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert datetime.fromisoformat(seen["created"]) == PAST
        assert datetime.fromisoformat(seen["last_modified"]) == last_modified

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_timestamps_in_whole_seconds(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}
    headers_b = {"Authorization": f"Bearer {admin_b.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Test client",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    post_json = r.json()
    assert_whole_seconds(post_json, "created")
    assert_whole_seconds(post_json, "last_modified")
    client_id = post_json["client_id"]
    client_url = r.headers["Location"]

    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
        },
        headers=headers_b,
    )
    assert r.status_code == 200
    patch_json = r.json()
    assert_whole_seconds(patch_json, "created")
    assert_whole_seconds(patch_json, "last_modified")

    r = await client.get(client_url, headers=headers_b)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients", headers=headers_b)
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert_whole_seconds(seen, "created")
        assert_whole_seconds(seen, "last_modified")

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_by_creator_keeps_creator_as_modifier(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    """Check a PATCH by the creator.

    The username part guards behaviour the ticket says is unchanged and holds
    on the code before the change too; the moved ``last_modified`` does not.
    """
    creator = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    headers = {"Authorization": f"Bearer {creator.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Test client",
        },
        headers=headers,
    )
    assert r.status_code == 201
    post_json = r.json()
    assert post_json["last_modified_by"] == "admin-a"
    client_url = r.headers["Location"]
    await backdate_client(client, factory, client_url, headers)

    before = datetime.now(tz=UTC).replace(microsecond=0)
    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated description",
            "notes": "Updated by the creator",
        },
        headers=headers,
    )
    after = datetime.now(tz=UTC)
    assert r.status_code == 200
    patch_json = r.json()
    assert "last_modified_by" in patch_json
    assert patch_json["last_modified_by"] == "admin-a"
    assert patch_json["created"] == "2020-01-01T12:00:00Z"
    assert "last_modified" in patch_json
    last_modified = datetime.fromisoformat(patch_json["last_modified"])
    assert before <= last_modified <= after

    r = await client.get(client_url, headers=headers)
    assert r.status_code == 200
    get_json = r.json()
    assert "last_modified_by" in get_json
    assert get_json["last_modified_by"] == "admin-a"
    assert get_json["notes"] == "Updated by the creator"
    assert get_json["created"] == "2020-01-01T12:00:00Z"
    assert get_json["last_modified"] == patch_json["last_modified"]

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_patch_by_other_admin_via_session_cookie(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Original description",
            "notes": "Notes to be cleared",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    created_json = r.json()
    assert created_json["last_modified_by"] == "admin-a"
    client_id = created_json["client_id"]
    client_url = r.headers["Location"]
    await backdate_client(client, factory, client_url, headers_a)

    # From here on, only the session cookie of the second administrator
    # authenticates the requests. A body without notes clears them.
    csrf = await set_session_cookie(client, admin_b.token)
    before = datetime.now(tz=UTC).replace(microsecond=0)
    r = await client.patch(
        client_url,
        json={
            "return_uri": "https://foo.example.com/other-service",
            "description": "Updated with a cookie",
        },
        headers={"X-CSRF-Token": csrf},
    )
    after = datetime.now(tz=UTC)
    assert r.status_code == 200
    patch_json = r.json()
    assert "last_modified_by" in patch_json
    assert patch_json["last_modified_by"] == "admin-b"
    assert patch_json["description"] == "Updated with a cookie"
    assert "notes" in patch_json
    assert patch_json["notes"] is None
    assert patch_json["created"] == "2020-01-01T12:00:00Z"
    last_modified = datetime.fromisoformat(patch_json["last_modified"])
    assert before <= last_modified <= after

    r = await client.get(client_url)
    assert r.status_code == 200
    get_json = r.json()
    r = await client.get("/auth/api/v1/oidc-clients")
    assert r.status_code == 200
    list_json = find_client(r.json(), client_id)
    for seen in (get_json, list_json):
        assert "last_modified_by" in seen
        assert seen["last_modified_by"] == "admin-b"
        assert seen["return_uri"] == "https://foo.example.com/other-service"
        assert seen["description"] == "Updated with a cookie"
        assert "notes" not in seen
        assert seen["created"] == "2020-01-01T12:00:00Z"
        assert seen["last_modified"] == patch_json["last_modified"]

    assert mock_slack.messages == []


@pytest.mark.parametrize("config", ["github-oidc-server"], indirect=True)
@pytest.mark.asyncio
async def test_refused_patch_leaves_client_unchanged(
    client: AsyncClient, factory: Factory, mock_slack: MockSlackWebhook
) -> None:
    """Check that refused PATCH requests change nothing.

    The ticket says these refusals do not change, so this is a deliberate
    regression guard that also passes on the code before the change.
    """
    admin_a = await create_session_token(
        factory, username="admin-a", scopes={"admin:oidc"}
    )
    admin_b = await create_session_token(
        factory, username="admin-b", scopes={"admin:oidc"}
    )
    user = await create_session_token(
        factory, username="some-user", scopes={"user:token"}
    )
    headers_a = {"Authorization": f"Bearer {admin_a.token}"}

    r = await client.post(
        "/auth/api/v1/oidc-clients",
        json={
            "return_uri": "https://foo.example.com/service/",
            "description": "Original description",
        },
        headers=headers_a,
    )
    assert r.status_code == 201
    client_url = r.headers["Location"]
    original = await backdate_client(client, factory, client_url, headers_a)
    assert original["last_modified_by"] == "admin-a"

    update = {
        "return_uri": "https://foo.example.com/other-service",
        "description": "Updated description",
        "notes": "Should never be stored",
    }
    r = await client.patch(client_url, json=update)
    assert r.status_code == 401
    r = await client.patch(
        client_url,
        json=update,
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert r.status_code == 403
    r = await client.patch(
        client_url,
        json={"return_uri": "https://foo.example.com/other-service"},
        headers={"Authorization": f"Bearer {admin_b.token}"},
    )
    assert r.status_code == 422
    r = await client.patch(
        client_url,
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {admin_b.token}"},
    )
    assert r.status_code == 422
    r = await client.patch(
        "/auth/api/v1/oidc-clients/unknown-client.clients.example.com",
        json=update,
        headers={"Authorization": f"Bearer {admin_b.token}"},
    )
    assert r.status_code == 404

    # The session cookie of an administrator without its CSRF token.
    await set_session_cookie(client, admin_b.token)
    r = await client.patch(client_url, json=update)
    assert r.status_code == 403
    clear_session_cookie(client)

    r = await client.get(client_url, headers=headers_a)
    assert r.status_code == 200
    assert r.json() == original

    assert mock_slack.messages == []
