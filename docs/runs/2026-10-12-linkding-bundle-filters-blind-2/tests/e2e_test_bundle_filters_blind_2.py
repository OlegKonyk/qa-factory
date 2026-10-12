from django.urls import reverse
from playwright.sync_api import expect

from bookmarks.models import BookmarkBundle
from bookmarks.tests_e2e.helpers import LinkdingE2ETestCase


class BundleReadingSharingStateE2ETestCase(LinkdingE2ETestCase):
    def setUp(self) -> None:
        super().setUp()
        profile = self.get_or_create_test_user().profile
        profile.enable_sharing = True
        profile.save()

        # Counts differ between every step of the tests below:
        # all = 7, unread = 3, unread + shared = 2, read + unshared = 3
        self.inbox_public = self.setup_numbered_bookmarks(
            2, prefix="Inbox Public", unread=True, shared=True
        )
        self.inbox_private = self.setup_numbered_bookmarks(
            1, prefix="Inbox Private", unread=True, shared=False
        )
        self.done_public = self.setup_numbered_bookmarks(
            1, prefix="Done Public", unread=False, shared=True
        )
        self.done_private = self.setup_numbered_bookmarks(
            3, prefix="Done Private", unread=False, shared=False
        )

    def locate_reading_state(self):
        return self.page.get_by_label("Reading State")

    def locate_sharing_state(self):
        return self.page.get_by_label("Sharing State")

    def assertStateDropdowns(self):
        reading_state = self.locate_reading_state()
        expect(reading_state).to_be_visible()
        expect(reading_state.locator("option")).to_have_text(["All", "Unread", "Read"])

        sharing_state = self.locate_sharing_state()
        expect(sharing_state).to_be_visible()
        expect(sharing_state.locator("option")).to_have_text(
            ["All", "Shared", "Unshared"]
        )

    def assertSelectedStates(self, reading: str, sharing: str):
        expect(self.locate_reading_state().locator("option:checked")).to_have_text(
            reading
        )
        expect(self.locate_sharing_state().locator("option:checked")).to_have_text(
            sharing
        )

    def assertPreviewCount(self, count: int):
        expect(
            self.page.get_by_text(f"Found {count} bookmarks matching this bundle")
        ).to_be_visible()

    def save_form(self):
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.get_by_text("Bundle saved successfully.")).to_be_visible()

    def open_bundle_bookmarks(self, bundle: BookmarkBundle):
        self.page.goto(
            self.live_server_url
            + reverse("linkding:bookmarks.index")
            + f"?bundle={bundle.id}"
        )

    def open_bundle_edit_form(self, bundle: BookmarkBundle):
        self.page.goto(
            self.live_server_url + reverse("linkding:bundles.edit", args=[bundle.id])
        )

    def test_create_bundle_with_reading_and_sharing_state(self):
        page = self.open(reverse("linkding:bundles.new"))

        self.assertStateDropdowns()
        self.assertSelectedStates("All", "All")
        self.assertPreviewCount(7)
        self.assertVisibleBookmarks(
            self.inbox_public
            + self.inbox_private
            + self.done_public
            + self.done_private
        )

        page.get_by_label("Name").fill("Unread and shared")

        self.locate_reading_state().select_option(label="Unread")
        self.assertPreviewCount(3)
        self.assertVisibleBookmarks(self.inbox_public + self.inbox_private)

        self.locate_sharing_state().select_option(label="Shared")
        self.assertPreviewCount(2)
        self.assertVisibleBookmarks(self.inbox_public)

        self.save_form()

        bundle = BookmarkBundle.objects.get(name="Unread and shared")

        # The bundle's bookmark list only shows matching bookmarks
        self.open_bundle_bookmarks(bundle)
        expect(self.locate_bookmark(self.inbox_public[0].title)).to_be_visible()
        self.assertVisibleBookmarks(self.inbox_public)

        # The edit form shows the stored selection
        self.open_bundle_edit_form(bundle)
        self.assertStateDropdowns()
        self.assertSelectedStates("Unread", "Shared")
        self.assertPreviewCount(2)

    def test_edit_bundle_reading_and_sharing_state(self):
        bundle = self.setup_bundle(name="Edited bundle")

        self.open(reverse("linkding:bundles.edit", args=[bundle.id]))

        self.assertStateDropdowns()
        self.assertSelectedStates("All", "All")
        self.assertPreviewCount(7)

        self.locate_reading_state().select_option(label="Read")
        self.locate_sharing_state().select_option(label="Unshared")
        self.assertPreviewCount(3)
        self.assertVisibleBookmarks(self.done_private)

        self.save_form()

        # The bundle's bookmark list only shows matching bookmarks
        self.open_bundle_bookmarks(bundle)
        expect(self.locate_bookmark(self.done_private[0].title)).to_be_visible()
        self.assertVisibleBookmarks(self.done_private)

        # The edit form shows the stored selection
        self.open_bundle_edit_form(bundle)
        self.assertSelectedStates("Read", "Unshared")
        self.assertPreviewCount(3)

    def assertVisibleBookmarks(self, bookmarks):
        self.assertEqual(len(bookmarks), self.count_bookmarks())

        for bookmark in bookmarks:
            expect(self.locate_bookmark(bookmark.title)).to_be_visible()
