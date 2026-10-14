"""The shipped sort-by-modified cases (docs/runs/2026-10-10-linkding-sort-by-modified-blind/testcases),
run against a deployed linkding with data created through the public REST API only."""

import re

import pytest
from playwright.sync_api import Page, expect


def ids(*bookmarks: dict) -> list[int]:
    return [b["id"] for b in bookmarks]


# TC-bookmarks-001
def test_list_bookmarks_sort_modified_asc_and_desc(bookmarks, sort_data):
    first, second, third = sort_data.sort_set()

    assert bookmarks.list_ids(q=sort_data.marker, sort="modified_asc") == ids(second, first, third)
    assert bookmarks.list_ids(q=sort_data.marker, sort="modified_desc") == ids(third, first, second)


# TC-bookmarks-002
def test_list_archived_bookmarks_sort_modified_asc_and_desc(bookmarks, sort_data):
    first, second, third = sort_data.sort_set(is_archived=True)
    # Non-archived bookmarks must not be included. Created after the edits, so it is the newest
    # modified (the in-suite test put it between second and first; what the case checks is that it
    # does not appear, and that holds wherever it sorts).
    sort_data.add("Not archived")

    asc = bookmarks.list_ids(q=sort_data.marker, sort="modified_asc", archived=True)
    assert asc == ids(second, first, third)
    desc = bookmarks.list_ids(q=sort_data.marker, sort="modified_desc", archived=True)
    assert desc == ids(third, first, second)


# TC-bookmarks-003
def test_list_bookmarks_unknown_sort_falls_back_to_added_desc(bookmarks, sort_data):
    first, second, third = sort_data.sort_set()
    a_first, a_second, a_third = sort_data.sort_set(is_archived=True)

    assert bookmarks.list_ids(q=sort_data.marker, sort="bogus") == ids(third, second, first)
    archived = bookmarks.list_ids(q=sort_data.marker, sort="bogus", archived=True)
    assert archived == ids(a_third, a_second, a_first)


@pytest.fixture
def logged_in_page(page: Page, credentials) -> Page:
    user, password = credentials
    page.goto("/login/")
    page.get_by_label("Username").fill(user)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()
    expect(page).not_to_have_url(re.compile(r"/login/"))
    return page


def expect_order(page: Page, *expected: dict) -> None:
    # The region also holds the pagination list; the bookmarks are its first list.
    region = page.get_by_role("region", name="Bookmark list", exact=True)
    items = region.get_by_role("list").first.get_by_role("listitem")
    expect(items).to_have_count(len(expected))
    for index, bookmark in enumerate(expected):
        expect(items.nth(index)).to_contain_text(bookmark["title"])


def open_search_preferences(page: Page):
    page.get_by_role("button", name="Search preferences").click()
    # Not get_by_label("Sort by"): once a sort is applied, linkding 1.47.0 renders the search form's
    # hidden `sort` input with the same id ("id_sort"), so the label names the hidden input.
    sort_select = page.get_by_role("main").get_by_role("combobox")
    expect(sort_select).to_be_visible()
    return sort_select


# TC-bookmarks-004
def test_sort_dropdown_modified_options_reorder_list(logged_in_page: Page, sort_data):
    page = logged_in_page
    first, second, third = sort_data.sort_set()
    marker = sort_data.marker

    page.goto(f"/bookmarks?q={marker}")
    expect_order(page, third, second, first)

    sort_select = open_search_preferences(page)
    expect(sort_select.locator("option").filter(has_text="Modified ↑")).to_have_count(1)
    expect(sort_select.locator("option").filter(has_text="Modified ↓")).to_have_count(1)

    sort_select.select_option(label="Modified ↑")
    page.get_by_role("button", name="Apply").click()
    expect(page).to_have_url(re.compile(rf"q={marker}"))
    expect_order(page, second, first, third)

    sort_select = open_search_preferences(page)
    sort_select.select_option(label="Modified ↓")
    page.get_by_role("button", name="Apply").click()
    expect(page).to_have_url(re.compile(rf"q={marker}"))
    expect_order(page, third, first, second)
