"""Fixtures for running the shipped sort-by-modified cases against a deployed linkding.

Everything the tests need comes from the environment and the public REST API: no ORM, no test
client, no access to the container. See README.md beside this file.
"""

import os
import time
import uuid
from datetime import datetime

import pytest
from playwright.sync_api import APIRequestContext, Playwright

DEFAULT_URL = "http://127.0.0.1:9090"

# The three bookmarks every case uses, in the order they are created (so in added order).
OLDEST_ADDED = "Oldest added, middle modified"
MIDDLE_ADDED = "Middle added, oldest modified"
NEWEST_ADDED = "Newest added, newest modified"


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} is not set; see targets/linkding/deployed/README.md")
    return value


@pytest.fixture(scope="session")
def base_url() -> str:
    """Overrides pytest-base-url's fixture, so `page.goto("/login/")` resolves against linkding."""
    return os.environ.get("LINKDING_URL", DEFAULT_URL).rstrip("/")


@pytest.fixture(scope="session")
def api(playwright: Playwright, base_url: str):
    token = _require("LINKDING_TOKEN")
    ctx = playwright.request.new_context(
        base_url=base_url,
        extra_http_headers={"Accept": "application/json", "Authorization": f"Token {token}"},
    )
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="session")
def credentials() -> tuple[str, str]:
    return _require("LINKDING_USER"), _require("LINKDING_PASSWORD")


def _when(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


class Bookmarks:
    """The bookmarks resource of linkding's REST API, as the tests use it."""

    def __init__(self, api: APIRequestContext):
        self.api = api

    def create(self, url: str, title: str, *, is_archived: bool = False) -> dict:
        r = self.api.post("/api/bookmarks/", data={"url": url, "title": title, "is_archived": is_archived})
        assert r.status == 201, f"create {url}: {r.status} {r.text()}"
        return r.json()

    def get(self, bookmark_id: int) -> dict:
        r = self.api.get(f"/api/bookmarks/{bookmark_id}/")
        assert r.ok, f"get {bookmark_id}: {r.status} {r.text()}"
        return r.json()

    def patch(self, bookmark_id: int, **fields) -> dict:
        r = self.api.patch(f"/api/bookmarks/{bookmark_id}/", data=fields)
        assert r.ok, f"patch {bookmark_id}: {r.status} {r.text()}"
        return r.json()

    def delete(self, bookmark_id: int) -> None:
        r = self.api.delete(f"/api/bookmarks/{bookmark_id}/")
        assert r.status in (204, 404), f"delete {bookmark_id}: {r.status} {r.text()}"

    def list_ids(self, *, q: str, sort: str, archived: bool = False) -> list[int]:
        path = "/api/bookmarks/archived/" if archived else "/api/bookmarks/"
        r = self.api.get(path, params={"q": q, "sort": sort, "limit": 100})
        assert r.status == 200, f"list {path} sort={sort}: {r.status} {r.text()}"
        return [item["id"] for item in r.json()["results"]]


class SortFixture:
    """Creates the cases' bookmarks for one test, under a marker unique to the test, and removes them.

    linkding's API cannot set `date_added` or `date_modified`. Added order is creation order;
    modified order is built by editing the bookmarks one after another, each edit confirmed by
    reading `date_modified` back as later than the previous edit's.
    """

    EDIT_DEADLINE_S = 5.0

    def __init__(self, bookmarks: Bookmarks):
        self.bookmarks = bookmarks
        self.marker = f"qaf{uuid.uuid4().hex[:12]}"
        self.created: list[int] = []
        self._n = 0
        self._last_modified: datetime | None = None

    def add(self, title: str, *, is_archived: bool = False) -> dict:
        self._n += 1
        url = f"https://example.com/{self.marker}/{self._n}"
        bookmark = self.bookmarks.create(url, f"{title} {self.marker}", is_archived=is_archived)
        self.created.append(bookmark["id"])
        return bookmark

    def touch(self, bookmark: dict) -> None:
        """Edit the bookmark so its `date_modified` is later than every earlier touch."""
        deadline = time.monotonic() + self.EDIT_DEADLINE_S
        attempt = 0
        while True:
            attempt += 1
            self.bookmarks.patch(bookmark["id"], description=f"edit {attempt}")
            modified = _when(self.bookmarks.get(bookmark["id"])["date_modified"])
            if self._last_modified is None or modified > self._last_modified:
                self._last_modified = modified
                return
            assert time.monotonic() < deadline, (
                f"date_modified of {bookmark['id']} did not move past {self._last_modified}"
            )

    def sort_set(self, *, is_archived: bool = False) -> tuple[dict, dict, dict]:
        """The three bookmarks of the cases: added first < second < third, modified second < first < third."""
        first = self.add(OLDEST_ADDED, is_archived=is_archived)
        second = self.add(MIDDLE_ADDED, is_archived=is_archived)
        third = self.add(NEWEST_ADDED, is_archived=is_archived)
        for bookmark in (second, first, third):
            self.touch(bookmark)
        return first, second, third

    def cleanup(self) -> None:
        for bookmark_id in reversed(self.created):
            self.bookmarks.delete(bookmark_id)


@pytest.fixture
def bookmarks(api: APIRequestContext) -> Bookmarks:
    return Bookmarks(api)


@pytest.fixture
def sort_data(bookmarks: Bookmarks):
    data = SortFixture(bookmarks)
    try:
        yield data
    finally:
        data.cleanup()
