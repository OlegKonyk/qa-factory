from django.urls import reverse
from playwright.sync_api import expect

from bookmarks.models import BookmarkBundle
from bookmarks.tests_e2e.helpers import LinkdingE2ETestCase


class BundleFilterStateE2ETestCase(LinkdingE2ETestCase):
    def setUp(self) -> None:
        super().setUp()
        user = self.get_or_create_test_user()
        user.profile.enable_sharing = True
        user.profile.save()

        # Each reading / sharing combination yields a different count
        self.unread_shared = self.setup_numbered_bookmarks(
            2, prefix="Kiwi", unread=True, shared=True
        )
        self.unread_unshared = self.setup_numbered_bookmarks(
            1, prefix="Lime", unread=True, shared=False
        )
        self.read_shared = self.setup_numbered_bookmarks(
            3, prefix="Mango", unread=False, shared=True
        )
        self.read_unshared = self.setup_numbered_bookmarks(
            2, prefix="Papaya", unread=False, shared=False
        )

    def locate_reading_state(self):
        return self.page.get_by_label("Reading State", exact=True)

    def locate_sharing_state(self):
        return self.page.get_by_label("Sharing State", exact=True)

    def assertStateControls(self, reading: str, sharing: str):
        reading_select = self.locate_reading_state()
        sharing_select = self.locate_sharing_state()
        expect(reading_select).to_be_visible()
        expect(sharing_select).to_be_visible()
        expect(reading_select.locator("option")).to_have_text(["All", "Unread", "Read"])
        expect(sharing_select.locator("option")).to_have_text(
            ["All", "Shared", "Unshared"]
        )
        expect(reading_select.locator("option:checked")).to_have_text(reading)
        expect(sharing_select.locator("option:checked")).to_have_text(sharing)

    def assertPreviewCount(self, count: int):
        expect(
            self.page.get_by_text(f"Found {count} bookmarks matching this bundle")
        ).to_be_visible()

    def assertVisibleBookmarks(self, bookmarks):
        self.assertEqual(len(bookmarks), self.count_bookmarks())

        for bookmark in bookmarks:
            expect(self.locate_bookmark(bookmark.title)).to_be_visible()

    def save_bundle(self):
        self.page.get_by_role("button", name="Save").click()
        expect(self.page.get_by_text("Bundle saved successfully.")).to_be_visible()

    def open_bundle_bookmarks(self, bundle: BookmarkBundle):
        self.page.goto(
            self.live_server_url
            + reverse("linkding:bookmarks.index")
            + f"?bundle={bundle.id}"
        )

    def test_create_bundle_with_reading_and_sharing_state(self):
        page = self.open(reverse("linkding:bundles.new"))

        self.assertPreviewCount(8)
        self.assertStateControls(reading="All", sharing="All")

        page.get_by_label("Name", exact=True).fill("Unread shared bundle")

        self.locate_reading_state().select_option(label="Unread")
        self.assertPreviewCount(3)
        self.assertVisibleBookmarks(self.unread_shared + self.unread_unshared)

        self.locate_sharing_state().select_option(label="Shared")
        self.assertPreviewCount(2)
        self.assertVisibleBookmarks(self.unread_shared)

        self.save_bundle()
        bundle = BookmarkBundle.objects.get(name="Unread shared bundle")

        # Edit form shows the stored selection
        page.goto(
            self.live_server_url
            + reverse("linkding:bundles.edit", kwargs={"bundle_id": bundle.id})
        )
        self.assertStateControls(reading="Unread", sharing="Shared")
        self.assertPreviewCount(2)

        # Bundle's bookmark list only shows matching bookmarks
        self.open_bundle_bookmarks(bundle)
        self.assertVisibleBookmarks(self.unread_shared)

    def test_edit_bundle_reading_and_sharing_state(self):
        bundle = self.setup_bundle(name="Existing bundle")
        page = self.open(
            reverse("linkding:bundles.edit", kwargs={"bundle_id": bundle.id})
        )

        self.assertPreviewCount(8)
        self.assertStateControls(reading="All", sharing="All")

        self.locate_reading_state().select_option(label="Read")
        self.assertPreviewCount(5)
        self.assertVisibleBookmarks(self.read_shared + self.read_unshared)

        self.locate_sharing_state().select_option(label="Unshared")
        self.assertPreviewCount(2)
        self.assertVisibleBookmarks(self.read_unshared)

        self.save_bundle()

        page.goto(
            self.live_server_url
            + reverse("linkding:bundles.edit", kwargs={"bundle_id": bundle.id})
        )
        self.assertStateControls(reading="Read", sharing="Unshared")

        self.open_bundle_bookmarks(bundle)
        self.assertVisibleBookmarks(self.read_unshared)
