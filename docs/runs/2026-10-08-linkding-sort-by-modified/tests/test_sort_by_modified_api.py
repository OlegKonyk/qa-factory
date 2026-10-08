import datetime

from django.urls import reverse
from django.utils import timezone

from bookmarks.tests.helpers import BookmarkFactoryMixin, LinkdingApiTestCase


class SortByModifiedApiTestCase(LinkdingApiTestCase, BookmarkFactoryMixin):
    def setup_sort_fixture(self, is_archived: bool = False):
        # Dates are chosen so that every sort order is distinct:
        #   added desc (default): c, b, a
        #   added asc:            a, b, c
        #   modified asc:         b, c, a
        #   modified desc:        a, c, b
        a = self.setup_bookmark(
            is_archived=is_archived,
            added=timezone.datetime(2020, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2022, 1, 1, tzinfo=datetime.UTC),
        )
        b = self.setup_bookmark(
            is_archived=is_archived,
            added=timezone.datetime(2021, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2020, 1, 1, tzinfo=datetime.UTC),
        )
        c = self.setup_bookmark(
            is_archived=is_archived,
            added=timezone.datetime(2022, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2021, 1, 1, tzinfo=datetime.UTC),
        )
        return a, b, c

    def get_result_ids(self, url):
        response = self.get(url)
        return [bookmark["id"] for bookmark in response.data["results"]]

    def test_list_bookmarks_sort_modified_asc(self):
        self.authenticate()
        a, b, c = self.setup_sort_fixture()

        ids = self.get_result_ids(
            reverse("linkding:bookmark-list") + "?sort=modified_asc"
        )

        self.assertEqual(ids, [b.id, c.id, a.id])

    def test_list_bookmarks_sort_modified_desc(self):
        self.authenticate()
        a, b, c = self.setup_sort_fixture()

        ids = self.get_result_ids(
            reverse("linkding:bookmark-list") + "?sort=modified_desc"
        )

        self.assertEqual(ids, [a.id, c.id, b.id])

    def test_list_archived_bookmarks_sort_modified_asc_and_desc(self):
        self.authenticate()
        a, b, c = self.setup_sort_fixture(is_archived=True)
        # unarchived bookmark modified in between the archived ones, must not
        # show up in either order
        self.setup_bookmark(
            added=timezone.datetime(2023, 1, 1, tzinfo=datetime.UTC),
            modified=timezone.datetime(2021, 6, 1, tzinfo=datetime.UTC),
        )

        ids = self.get_result_ids(
            reverse("linkding:bookmark-archived") + "?sort=modified_asc"
        )
        self.assertEqual(ids, [b.id, c.id, a.id])

        ids = self.get_result_ids(
            reverse("linkding:bookmark-archived") + "?sort=modified_desc"
        )
        self.assertEqual(ids, [a.id, c.id, b.id])

    def test_list_bookmarks_unknown_sort_falls_back_to_default_order(self):
        self.authenticate()
        a, b, c = self.setup_sort_fixture()

        ids = self.get_result_ids(reverse("linkding:bookmark-list") + "?sort=bogus")

        # default order is date added, newest first
        self.assertEqual(ids, [c.id, b.id, a.id])
