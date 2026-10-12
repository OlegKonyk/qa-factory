from django.urls import reverse
from rest_framework import status

from bookmarks.tests.helpers import (
    BookmarkFactoryMixin,
    BookmarkListTestMixin,
    LinkdingApiTestCase,
)


class BundleReadingSharingFiltersApiTestCase(
    LinkdingApiTestCase, BookmarkFactoryMixin, BookmarkListTestMixin
):
    def create_bundle(self, data: dict) -> int:
        url = reverse("linkding:bundle-list")
        response = self.post(url, data, expected_status_code=status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        return response.data["id"]

    def get_bundle_data(self, bundle_id: int) -> dict:
        url = reverse("linkding:bundle-detail", kwargs={"pk": bundle_id})
        response = self.get(url, expected_status_code=status.HTTP_200_OK)
        return response.data

    def assertFilters(self, data: dict, filter_unread: str, filter_shared: str):
        self.assertIn("filter_unread", data)
        self.assertIn("filter_shared", data)
        self.assertEqual(data["filter_unread"], filter_unread)
        self.assertEqual(data["filter_shared"], filter_shared)

    def assertBookmarksForBundle(self, bundle_id: int, expected_bookmarks):
        response = self.get(
            reverse("linkding:bookmark-list") + f"?bundle={bundle_id}",
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertIn("results", response.data)
        returned_ids = sorted(item["id"] for item in response.data["results"])
        expected_ids = sorted(bookmark.id for bookmark in expected_bookmarks)
        self.assertEqual(returned_ids, expected_ids)

    def test_create_and_get_bundle_with_filter_unread_and_filter_shared(self):
        self.authenticate()

        unread_bundle_id = self.create_bundle(
            {
                "name": "Unread unshared",
                "search": "python",
                "filter_unread": "yes",
                "filter_shared": "no",
            }
        )
        read_bundle_id = self.create_bundle(
            {
                "name": "Read shared",
                "search": "python",
                "filter_unread": "no",
                "filter_shared": "yes",
            }
        )
        default_bundle_id = self.create_bundle({"name": "Defaults"})

        self.assertFilters(self.get_bundle_data(unread_bundle_id), "yes", "no")
        self.assertFilters(self.get_bundle_data(read_bundle_id), "no", "yes")
        self.assertFilters(self.get_bundle_data(default_bundle_id), "off", "off")

        # The list endpoint carries the fields as well
        response = self.get(
            reverse("linkding:bundle-list"), expected_status_code=status.HTTP_200_OK
        )
        results_by_id = {item["id"]: item for item in response.data["results"]}
        self.assertIn(unread_bundle_id, results_by_id)
        self.assertIn(default_bundle_id, results_by_id)
        self.assertFilters(results_by_id[unread_bundle_id], "yes", "no")
        self.assertFilters(results_by_id[default_bundle_id], "off", "off")

    def test_patch_bundle_changes_filter_fields_and_keeps_others(self):
        self.authenticate()

        bundle_id = self.create_bundle(
            {
                "name": "Patched bundle",
                "search": "python",
                "any_tags": "programming",
                "all_tags": "required",
                "excluded_tags": "excluded",
            }
        )
        url = reverse("linkding:bundle-detail", kwargs={"pk": bundle_id})

        # Changing only the reading state leaves the sharing state as it was
        self.patch(
            url, {"filter_unread": "no"}, expected_status_code=status.HTTP_200_OK
        )
        self.assertFilters(self.get_bundle_data(bundle_id), "no", "off")

        # Changing only the sharing state leaves the reading state as it was
        self.patch(
            url, {"filter_shared": "yes"}, expected_status_code=status.HTTP_200_OK
        )
        self.assertFilters(self.get_bundle_data(bundle_id), "no", "yes")

        # Changing both at once
        self.patch(
            url,
            {"filter_unread": "yes", "filter_shared": "no"},
            expected_status_code=status.HTTP_200_OK,
        )
        data = self.get_bundle_data(bundle_id)
        self.assertFilters(data, "yes", "no")
        self.assertEqual(data["name"], "Patched bundle")
        self.assertEqual(data["search"], "python")
        self.assertEqual(data["any_tags"], "programming")
        self.assertEqual(data["all_tags"], "required")
        self.assertEqual(data["excluded_tags"], "excluded")

        # Turning both off again
        self.patch(
            url,
            {"filter_unread": "off", "filter_shared": "off"},
            expected_status_code=status.HTTP_200_OK,
        )
        self.assertFilters(self.get_bundle_data(bundle_id), "off", "off")

    def test_bookmarks_by_bundle_filter_unread_yes_no_off(self):
        self.authenticate()
        search_value = self.get_random_string()
        unread_matching = self.setup_numbered_bookmarks(
            3, prefix=search_value + " unread", unread=True
        )
        read_matching = self.setup_numbered_bookmarks(
            2, prefix=search_value + " read", unread=False
        )
        # Bookmarks that do not match the bundle's search
        self.setup_numbered_bookmarks(2, prefix="other unread", unread=True)
        self.setup_numbered_bookmarks(2, prefix="other read", unread=False)

        unread_yes_id = self.create_bundle(
            {"name": "Unread", "search": search_value, "filter_unread": "yes"}
        )
        unread_no_id = self.create_bundle(
            {"name": "Read", "search": search_value, "filter_unread": "no"}
        )
        unread_off_id = self.create_bundle(
            {"name": "All", "search": search_value, "filter_unread": "off"}
        )

        self.assertBookmarksForBundle(unread_yes_id, unread_matching)
        self.assertBookmarksForBundle(unread_no_id, read_matching)
        self.assertBookmarksForBundle(unread_off_id, unread_matching + read_matching)

    def test_bookmarks_by_bundle_filter_shared_yes_no_off(self):
        self.authenticate()
        search_value = self.get_random_string()
        shared_matching = self.setup_numbered_bookmarks(
            3, prefix=search_value + " shared", shared=True
        )
        unshared_matching = self.setup_numbered_bookmarks(
            2, prefix=search_value + " unshared", shared=False
        )
        # Bookmarks that do not match the bundle's search
        self.setup_numbered_bookmarks(2, prefix="other shared", shared=True)
        self.setup_numbered_bookmarks(2, prefix="other unshared", shared=False)

        shared_yes_id = self.create_bundle(
            {"name": "Shared", "search": search_value, "filter_shared": "yes"}
        )
        shared_no_id = self.create_bundle(
            {"name": "Unshared", "search": search_value, "filter_shared": "no"}
        )
        shared_off_id = self.create_bundle(
            {"name": "All", "search": search_value, "filter_shared": "off"}
        )

        self.assertBookmarksForBundle(shared_yes_id, shared_matching)
        self.assertBookmarksForBundle(shared_no_id, unshared_matching)
        self.assertBookmarksForBundle(
            shared_off_id, shared_matching + unshared_matching
        )

    def test_bookmarks_by_bundle_combines_unread_shared_search_and_tags(self):
        self.authenticate()
        search_value = self.get_random_string()
        required_tag = self.setup_tag(name="required")
        excluded_tag = self.setup_tag(name="excluded")

        # Match search and tags, cover all four reading / sharing combinations
        unread_shared = self.setup_bookmark(
            title=f"{search_value} unread shared",
            unread=True,
            shared=True,
            tags=[required_tag],
        )
        unread_unshared = self.setup_bookmark(
            title=f"{search_value} unread unshared",
            unread=True,
            shared=False,
            tags=[required_tag],
        )
        read_shared = self.setup_bookmark(
            title=f"{search_value} read shared",
            unread=False,
            shared=True,
            tags=[required_tag],
        )
        read_unshared = self.setup_bookmark(
            title=f"{search_value} read unshared",
            unread=False,
            shared=False,
            tags=[required_tag],
        )
        # Unread and shared, but each fails one of the other conditions
        fails_search = self.setup_bookmark(
            title="no search term", unread=True, shared=True, tags=[required_tag]
        )
        fails_required_tag = self.setup_bookmark(
            title=f"{search_value} without tag", unread=True, shared=True
        )
        fails_excluded_tag = self.setup_bookmark(
            title=f"{search_value} with excluded tag",
            unread=True,
            shared=True,
            tags=[required_tag, excluded_tag],
        )
        # Read and unshared, but each fails one of the other conditions
        read_unshared_fails_search = self.setup_bookmark(
            title="also no search term",
            unread=False,
            shared=False,
            tags=[required_tag],
        )
        read_unshared_fails_tag = self.setup_bookmark(
            title=f"{search_value} read unshared without tag",
            unread=False,
            shared=False,
        )
        all_bookmarks = [
            unread_shared,
            unread_unshared,
            read_shared,
            read_unshared,
            fails_search,
            fails_required_tag,
            fails_excluded_tag,
            read_unshared_fails_search,
            read_unshared_fails_tag,
        ]

        unread_shared_bundle_id = self.create_bundle(
            {
                "name": "Unread and shared",
                "search": search_value,
                "all_tags": "required",
                "excluded_tags": "excluded",
                "filter_unread": "yes",
                "filter_shared": "yes",
            }
        )
        read_unshared_bundle_id = self.create_bundle(
            {
                "name": "Read and unshared",
                "search": search_value,
                "all_tags": "required",
                "excluded_tags": "excluded",
                "filter_unread": "no",
                "filter_shared": "no",
            }
        )
        unread_any_sharing_bundle_id = self.create_bundle(
            {
                "name": "Unread, any sharing state",
                "search": search_value,
                "all_tags": "required",
                "excluded_tags": "excluded",
                "filter_unread": "yes",
                "filter_shared": "off",
            }
        )

        self.assertBookmarksForBundle(unread_shared_bundle_id, [unread_shared])
        self.assertBookmarksForBundle(read_unshared_bundle_id, [read_unshared])
        self.assertBookmarksForBundle(
            unread_any_sharing_bundle_id, [unread_shared, unread_unshared]
        )

        # The bookmark list page applies the same conditions
        self.client.force_login(self.get_or_create_test_user())

        response = self.client.get(
            reverse("linkding:bookmarks.index") + f"?bundle={unread_shared_bundle_id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVisibleBookmarks(response, [unread_shared])
        self.assertInvisibleBookmarks(
            response, [b for b in all_bookmarks if b is not unread_shared]
        )

        response = self.client.get(
            reverse("linkding:bookmarks.index") + f"?bundle={read_unshared_bundle_id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertVisibleBookmarks(response, [read_unshared])
        self.assertInvisibleBookmarks(
            response, [b for b in all_bookmarks if b is not read_unshared]
        )
