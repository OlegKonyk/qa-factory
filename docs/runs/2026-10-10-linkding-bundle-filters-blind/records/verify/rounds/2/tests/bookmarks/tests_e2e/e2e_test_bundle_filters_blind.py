import os

from django.contrib.staticfiles.testing import LiveServerTestCase
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import Page, expect, sync_playwright

from bookmarks.models import Bookmark, BookmarkBundle, User

# Allow Django ORM operations within Playwright's async context
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


# LinkdingE2ETestCase is not used: its module imports bookmarks/tests/helpers.py,
# whose setup_bundle defaults read a bundle constant at import time, so importing
# it crashes before the feature exists instead of letting these tests fail on an
# assertion. This class mirrors the parts of it that the tests need.
class BundleFilterStateE2ETestCase(LiveServerTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.user.profile.enable_sharing = True
        self.user.profile.save()
        self.client.force_login(self.user)
        self.cookie = self.client.cookies["sessionid"]
        self.playwright = None
        self.browser = None
        self.page = None

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

    def tearDown(self) -> None:
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        super().tearDown()

    def setup_numbered_bookmarks(
        self, count: int, prefix: str, unread: bool, shared: bool
    ):
        bookmarks = []
        for i in range(1, count + 1):
            bookmark = Bookmark(
                url=f"https://example.com/{prefix}/{i}",
                title=f"{prefix} {i}",
                date_added=timezone.now(),
                date_modified=timezone.now(),
                owner=self.user,
                unread=unread,
                shared=shared,
            )
            bookmark.save()
            bookmarks.append(bookmark)
        return bookmarks

    def setup_bundle(self, name: str):
        # Only the conditions that exist without the feature, like a bundle
        # saved before the change
        bundle = BookmarkBundle(name=name, owner=self.user)
        bundle.save()
        return bundle

    def open(self, url: str) -> Page:
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        context = self.browser.new_context()
        context.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": self.cookie.value,
                    "domain": self.live_server_url.replace("http:", ""),
                    "path": "/",
                }
            ]
        )
        self.page = context.new_page()
        self.page.goto(self.live_server_url + url)
        return self.page

    def locate_bookmark(self, title: str):
        return self.page.locator("ul.bookmark-list > li").filter(has_text=title)

    def count_bookmarks(self):
        return self.page.locator("ul.bookmark-list > li").count()

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
