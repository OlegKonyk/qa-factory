from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from bookmarks.tests_e2e.helpers import LinkdingE2ETestCase


class SortByModifiedE2ETestCase(LinkdingE2ETestCase):
    def setup_fixture(self):
        # Added order: first < second < third
        # Modified order: second < first < third
        # So neither modified order matches the default (added, newest first).
        now = timezone.now()
        self.setup_bookmark(
            title="Oldest added, middle modified",
            added=now - timedelta(days=30),
            modified=now - timedelta(days=5),
        )
        self.setup_bookmark(
            title="Middle added, oldest modified",
            added=now - timedelta(days=20),
            modified=now - timedelta(days=10),
        )
        self.setup_bookmark(
            title="Newest added, newest modified",
            added=now - timedelta(days=10),
            modified=now - timedelta(days=1),
        )

    def locate_search_preferences(self):
        return self.page.locator("ld-dropdown").filter(
            has=self.page.get_by_role("button", name="Search preferences")
        )

    def open_search_preferences(self):
        dropdown = self.locate_search_preferences()
        dropdown.get_by_role("button", name="Search preferences").click()
        sort_select = dropdown.locator('select[name="sort"]')
        expect(sort_select).to_be_visible()
        return sort_select

    def apply_search_preferences(self):
        self.locate_search_preferences().get_by_role("button", name="Apply").click()

    def assertBookmarkOrder(self, titles: list[str]):
        bookmark_tags = self.page.locator("ul.bookmark-list > li")
        expect(bookmark_tags).to_have_count(len(titles))
        for index, title in enumerate(titles):
            expect(bookmark_tags.nth(index)).to_contain_text(title)

    def test_sort_dropdown_modified_options_reorder_list(self):
        self.setup_fixture()
        self.open(reverse("linkding:bookmarks.index"))

        # Default order: added, newest first
        self.assertBookmarkOrder(
            [
                "Newest added, newest modified",
                "Middle added, oldest modified",
                "Oldest added, middle modified",
            ]
        )

        # The sort dropdown offers both modification date options
        sort_select = self.open_search_preferences()
        expect(
            sort_select.locator("option").filter(has_text="Modified ↑")
        ).to_have_count(1)
        expect(
            sort_select.locator("option").filter(has_text="Modified ↓")
        ).to_have_count(1)

        # Modified ascending
        sort_select.select_option(label="Modified ↑")
        self.apply_search_preferences()
        self.assertBookmarkOrder(
            [
                "Middle added, oldest modified",
                "Oldest added, middle modified",
                "Newest added, newest modified",
            ]
        )

        # Modified descending
        sort_select = self.open_search_preferences()
        sort_select.select_option(label="Modified ↓")
        self.apply_search_preferences()
        self.assertBookmarkOrder(
            [
                "Newest added, newest modified",
                "Oldest added, middle modified",
                "Middle added, oldest modified",
            ]
        )
