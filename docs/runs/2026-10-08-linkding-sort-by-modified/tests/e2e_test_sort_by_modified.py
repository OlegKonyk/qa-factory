import datetime
import re

from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from bookmarks.tests_e2e.helpers import LinkdingE2ETestCase


class SortByModifiedE2ETestCase(LinkdingE2ETestCase):
    def setup_sort_fixture(self, is_archived: bool = False):
        # Dates are chosen so that every sort order is distinct:
        #   added desc (default): Charlie, Bravo, Alpha
        #   modified asc:         Bravo, Charlie, Alpha
        #   modified desc:        Alpha, Charlie, Bravo
        self.setup_bookmark(
            title="Alpha",
            is_archived=is_archived,
            added=timezone.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        self.setup_bookmark(
            title="Bravo",
            is_archived=is_archived,
            added=timezone.datetime(2021, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        )
        self.setup_bookmark(
            title="Charlie",
            is_archived=is_archived,
            added=timezone.datetime(2022, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2021, 1, 1, tzinfo=datetime.UTC),
        )

    def locate_bookmark_titles(self):
        return self.page.locator("ul.bookmark-list > li .title a span")

    def open_sort_select(self):
        self.page.get_by_role("button", name="Search preferences").click()
        menu = self.page.locator(".search-options .menu")
        expect(menu).to_be_visible()
        # not using get_by_label: once a sort is applied, the search form's
        # hidden sort input shares the select's id
        return menu, menu.locator('select[name="sort"]')

    def apply_sort(self, label: str):
        menu, sort_select = self.open_sort_select()
        expect(sort_select.locator("option")).to_contain_text(
            ["Modified ↑", "Modified ↓"]
        )
        sort_select.select_option(label=label)
        menu.get_by_role("button", name="Apply").click()

    def test_sort_bookmarks_by_modified_asc_and_desc(self):
        self.setup_sort_fixture()

        self.open(reverse("linkding:bookmarks.index"))
        expect(self.locate_bookmark_titles()).to_have_text(
            ["Charlie", "Bravo", "Alpha"]
        )

        self.apply_sort("Modified ↑")
        expect(self.page).to_have_url(re.compile(r"[?&]sort=modified_asc"))
        expect(self.locate_bookmark_titles()).to_have_text(
            ["Bravo", "Charlie", "Alpha"]
        )

        self.apply_sort("Modified ↓")
        expect(self.page).to_have_url(re.compile(r"[?&]sort=modified_desc"))
        expect(self.locate_bookmark_titles()).to_have_text(
            ["Alpha", "Charlie", "Bravo"]
        )

    def test_sort_archived_bookmarks_by_modified(self):
        self.setup_sort_fixture(is_archived=True)

        self.open(reverse("linkding:bookmarks.archived"))
        expect(self.locate_bookmark_titles()).to_have_text(
            ["Charlie", "Bravo", "Alpha"]
        )

        self.apply_sort("Modified ↓")
        expect(self.page).to_have_url(re.compile(r"[?&]sort=modified_desc"))
        expect(self.locate_bookmark_titles()).to_have_text(
            ["Alpha", "Charlie", "Bravo"]
        )
