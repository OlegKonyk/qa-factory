from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from bookmarks.tests.helpers import BookmarkFactoryMixin, LinkdingApiTestCase


class SortByModifiedApiTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def setup_sort_fixture(self, is_archived: bool = False):
        # Added order: first < second < third
        # Modified order: second < first < third
        # So neither modified order matches the added or title order.
        now = timezone.now()
        first = self.setup_bookmark(
            title="Oldest added, middle modified",
            is_archived=is_archived,
            added=now - timedelta(days=30),
            modified=now - timedelta(days=5),
        )
        second = self.setup_bookmark(
            title="Middle added, oldest modified",
            is_archived=is_archived,
            added=now - timedelta(days=20),
            modified=now - timedelta(days=10),
        )
        third = self.setup_bookmark(
            title="Newest added, newest modified",
            is_archived=is_archived,
            added=now - timedelta(days=10),
            modified=now - timedelta(days=1),
        )
        return first, second, third

    def assertResultOrder(self, response, expected_bookmarks):
        self.assertIn("results", response.data)
        result_ids = []
        for item in response.data["results"]:
            self.assertIn("id", item)
            result_ids.append(item["id"])
        expected_ids = [bookmark.id for bookmark in expected_bookmarks]
        self.assertEqual(result_ids, expected_ids)

    def test_list_bookmarks_sort_modified_asc_and_desc(self):
        self.authenticate()
        first, second, third = self.setup_sort_fixture()
        # Bookmarks of other users must not be included
        other_user = self.setup_user()
        self.setup_bookmark(
            user=other_user,
            added=timezone.now() - timedelta(days=15),
            modified=timezone.now() - timedelta(days=7),
        )

        response = self.get(
            reverse("linkding:bookmark-list") + "?sort=modified_asc",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertResultOrder(response, [second, first, third])

        response = self.get(
            reverse("linkding:bookmark-list") + "?sort=modified_desc",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertResultOrder(response, [third, first, second])

    def test_list_archived_bookmarks_sort_modified_asc_and_desc(self):
        self.authenticate()
        first, second, third = self.setup_sort_fixture(is_archived=True)
        # Non-archived bookmarks must not be included
        self.setup_bookmark(
            added=timezone.now() - timedelta(days=15),
            modified=timezone.now() - timedelta(days=7),
        )

        response = self.get(
            reverse("linkding:bookmark-archived") + "?sort=modified_asc",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertResultOrder(response, [second, first, third])

        response = self.get(
            reverse("linkding:bookmark-archived") + "?sort=modified_desc",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertResultOrder(response, [third, first, second])

    def test_list_bookmarks_unknown_sort_falls_back_to_added_desc(self):
        self.authenticate()
        first, second, third = self.setup_sort_fixture()
        archived_first, archived_second, archived_third = self.setup_sort_fixture(
            is_archived=True
        )

        response = self.get(
            reverse("linkding:bookmark-list") + "?sort=bogus",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertResultOrder(response, [third, second, first])

        response = self.get(
            reverse("linkding:bookmark-archived") + "?sort=bogus",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertResultOrder(
            response, [archived_third, archived_second, archived_first]
        )
