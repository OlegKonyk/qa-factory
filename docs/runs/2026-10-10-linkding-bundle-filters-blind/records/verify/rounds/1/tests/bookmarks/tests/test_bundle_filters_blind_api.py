from django.urls import reverse
from rest_framework import status

from bookmarks.models import BookmarkBundle
from bookmarks.tests.helpers import (
    BookmarkFactoryMixin,
    BookmarkListTestMixin,
    LinkdingApiTestCase,
)


class BundleFilterStateApiTestCase(
    LinkdingApiTestCase, BookmarkFactoryMixin, BookmarkListTestMixin
):
    def create_bundle(self, data: dict) -> int:
        url = reverse("linkding:bundle-list")
        response = self.post(url, data, expected_status_code=status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        return response.data["id"]

    def get_bundle(self, bundle_id: int) -> dict:
        url = reverse("linkding:bundle-detail", kwargs={"pk": bundle_id})
        return self.get(url, expected_status_code=status.HTTP_200_OK).data

    def assertFilterState(self, data: dict, filter_unread: str, filter_shared: str):
        self.assertIn("filter_unread", data)
        self.assertIn("filter_shared", data)
        self.assertEqual(data["filter_unread"], filter_unread)
        self.assertEqual(data["filter_shared"], filter_shared)

    def get_bundle_bookmark_titles(self, bundle_id: int) -> set:
        url = reverse("linkding:bookmark-list") + f"?bundle={bundle_id}"
        response = self.get(url, expected_status_code=status.HTTP_200_OK)
        return {bookmark["title"] for bookmark in response.data["results"]}

    def test_create_and_get_bundle_returns_filter_unread_and_filter_shared(self):
        self.authenticate()

        bundle_id = self.create_bundle(
            {
                "name": "Bundle with states",
                "search": "foo",
                "filter_unread": "yes",
                "filter_shared": "no",
            }
        )

        self.assertFilterState(self.get_bundle(bundle_id), "yes", "no")

        list_response = self.get(
            reverse("linkding:bundle-list"), expected_status_code=status.HTTP_200_OK
        )
        listed = [b for b in list_response.data["results"] if b["id"] == bundle_id]
        self.assertEqual(len(listed), 1)
        self.assertFilterState(listed[0], "yes", "no")

        bundle_id = self.create_bundle(
            {
                "name": "Bundle with other states",
                "filter_unread": "no",
                "filter_shared": "yes",
            }
        )

        self.assertFilterState(self.get_bundle(bundle_id), "no", "yes")

    def test_create_bundle_without_states_defaults_to_off(self):
        self.authenticate()

        bundle_id = self.create_bundle({"name": "Bundle without states"})

        self.assertFilterState(self.get_bundle(bundle_id), "off", "off")

    def test_patch_bundle_changes_filter_unread_and_filter_shared(self):
        self.authenticate()
        bundle = self.setup_bundle(name="Existing bundle", search="foo")
        url = reverse("linkding:bundle-detail", kwargs={"pk": bundle.id})

        self.assertFilterState(self.get_bundle(bundle.id), "off", "off")

        self.patch(url, {"filter_unread": "yes"})
        self.assertFilterState(self.get_bundle(bundle.id), "yes", "off")

        self.patch(url, {"filter_shared": "no"})
        self.assertFilterState(self.get_bundle(bundle.id), "yes", "no")

        self.patch(url, {"filter_unread": "no", "filter_shared": "yes"})
        self.assertFilterState(self.get_bundle(bundle.id), "no", "yes")

        self.patch(url, {"filter_unread": "off", "filter_shared": "off"})
        self.assertFilterState(self.get_bundle(bundle.id), "off", "off")

        # Other bundle conditions are untouched by the patches
        data = self.get_bundle(bundle.id)
        self.assertEqual(data["name"], "Existing bundle")
        self.assertEqual(data["search"], "foo")

    def test_put_bundle_sets_filter_unread_and_filter_shared(self):
        self.authenticate()
        bundle = self.setup_bundle(name="Existing bundle", search="foo")
        url = reverse("linkding:bundle-detail", kwargs={"pk": bundle.id})

        self.put(
            url,
            {
                "name": "Updated bundle",
                "search": "bar",
                "any_tags": "",
                "all_tags": "",
                "excluded_tags": "",
                "order": 0,
                "filter_unread": "no",
                "filter_shared": "yes",
            },
        )

        data = self.get_bundle(bundle.id)
        self.assertFilterState(data, "no", "yes")
        self.assertEqual(data["name"], "Updated bundle")

    def test_bookmarks_api_bundle_filter_unread_yes_no_off(self):
        self.authenticate()
        self.setup_bookmark(title="match unread one", unread=True, shared=True)
        self.setup_bookmark(title="match unread two", unread=True)
        self.setup_bookmark(title="match read one", unread=False, shared=True)
        self.setup_bookmark(title="match read two", unread=False)
        self.setup_bookmark(title="other unread", unread=True)
        self.setup_bookmark(title="other read", unread=False)

        unread_bundle = self.create_bundle(
            {"name": "Unread", "search": "match", "filter_unread": "yes"}
        )
        read_bundle = self.create_bundle(
            {"name": "Read", "search": "match", "filter_unread": "no"}
        )
        all_bundle = self.create_bundle(
            {"name": "All", "search": "match", "filter_unread": "off"}
        )

        self.assertEqual(
            self.get_bundle_bookmark_titles(unread_bundle),
            {"match unread one", "match unread two"},
        )
        self.assertEqual(
            self.get_bundle_bookmark_titles(read_bundle),
            {"match read one", "match read two"},
        )
        self.assertEqual(
            self.get_bundle_bookmark_titles(all_bundle),
            {
                "match unread one",
                "match unread two",
                "match read one",
                "match read two",
            },
        )

    def test_bookmarks_api_bundle_filter_shared_yes_no_off(self):
        self.authenticate()
        self.setup_bookmark(title="match shared one", shared=True, unread=True)
        self.setup_bookmark(title="match shared two", shared=True)
        self.setup_bookmark(title="match unshared one", shared=False, unread=True)
        self.setup_bookmark(title="match unshared two", shared=False)
        self.setup_bookmark(title="other shared", shared=True)
        self.setup_bookmark(title="other unshared", shared=False)

        shared_bundle = self.create_bundle(
            {"name": "Shared", "search": "match", "filter_shared": "yes"}
        )
        unshared_bundle = self.create_bundle(
            {"name": "Unshared", "search": "match", "filter_shared": "no"}
        )
        all_bundle = self.create_bundle(
            {"name": "All", "search": "match", "filter_shared": "off"}
        )

        self.assertEqual(
            self.get_bundle_bookmark_titles(shared_bundle),
            {"match shared one", "match shared two"},
        )
        self.assertEqual(
            self.get_bundle_bookmark_titles(unshared_bundle),
            {"match unshared one", "match unshared two"},
        )
        self.assertEqual(
            self.get_bundle_bookmark_titles(all_bundle),
            {
                "match shared one",
                "match shared two",
                "match unshared one",
                "match unshared two",
            },
        )

    def test_bookmarks_api_bundle_without_states_matches_all_states(self):
        # Fallback: a bundle created before the change still matches read,
        # unread, shared and unshared bookmarks
        self.authenticate()
        self.setup_bookmark(title="match unread shared", unread=True, shared=True)
        self.setup_bookmark(title="match unread unshared", unread=True)
        self.setup_bookmark(title="match read shared", shared=True)
        self.setup_bookmark(title="match read unshared")
        self.setup_bookmark(title="other")
        bundle = self.setup_bundle(search="match")

        self.assertEqual(
            self.get_bundle_bookmark_titles(bundle.id),
            {
                "match unread shared",
                "match unread unshared",
                "match read shared",
                "match read unshared",
            },
        )

    def test_bookmarks_api_bundle_combines_states_with_search_and_tags(self):
        self.authenticate()
        tag_required = self.setup_tag(name="required")
        tag_excluded = self.setup_tag(name="excluded")

        # Each decoy fails exactly one of the bundle's conditions
        self.setup_bookmark(
            title="match unread shared",
            unread=True,
            shared=True,
            tags=[tag_required],
        )
        self.setup_bookmark(
            title="match read unshared",
            unread=False,
            shared=False,
            tags=[tag_required],
        )
        self.setup_bookmark(
            title="match read shared",
            unread=False,
            shared=True,
            tags=[tag_required],
        )
        self.setup_bookmark(
            title="match unread unshared",
            unread=True,
            shared=False,
            tags=[tag_required],
        )
        self.setup_bookmark(
            title="no search term unread shared",
            unread=True,
            shared=True,
            tags=[tag_required],
        )
        self.setup_bookmark(
            title="match unread shared untagged",
            unread=True,
            shared=True,
        )
        self.setup_bookmark(
            title="match unread shared excluded",
            unread=True,
            shared=True,
            tags=[tag_required, tag_excluded],
        )
        self.setup_bookmark(
            title="match read unshared untagged",
            unread=False,
            shared=False,
        )
        self.setup_bookmark(
            title="match read unshared excluded",
            unread=False,
            shared=False,
            tags=[tag_required, tag_excluded],
        )

        unread_shared_bundle = self.create_bundle(
            {
                "name": "Unread and shared",
                "search": "match",
                "all_tags": "required",
                "excluded_tags": "excluded",
                "filter_unread": "yes",
                "filter_shared": "yes",
            }
        )
        read_unshared_bundle = self.create_bundle(
            {
                "name": "Read and unshared",
                "search": "match",
                "all_tags": "required",
                "excluded_tags": "excluded",
                "filter_unread": "no",
                "filter_shared": "no",
            }
        )
        unread_unshared_bundle = self.create_bundle(
            {
                "name": "Unread and unshared, any tag",
                "search": "match",
                "any_tags": "required excluded",
                "filter_unread": "yes",
                "filter_shared": "no",
            }
        )

        self.assertEqual(
            self.get_bundle_bookmark_titles(unread_shared_bundle),
            {"match unread shared"},
        )
        self.assertEqual(
            self.get_bundle_bookmark_titles(read_unshared_bundle),
            {"match read unshared"},
        )
        self.assertEqual(
            self.get_bundle_bookmark_titles(unread_unshared_bundle),
            {"match unread unshared"},
        )

    def test_bookmark_list_page_bundle_applies_unread_and_shared_conditions(self):
        self.authenticate()
        self.client.force_login(self.get_or_create_test_user())
        unread_shared = self.setup_bookmark(
            title="match unread shared", unread=True, shared=True
        )
        unread_unshared = self.setup_bookmark(
            title="match unread unshared", unread=True, shared=False
        )
        read_shared = self.setup_bookmark(
            title="match read shared", unread=False, shared=True
        )
        read_unshared = self.setup_bookmark(
            title="match read unshared", unread=False, shared=False
        )
        other = self.setup_bookmark(
            title="other unread shared", unread=True, shared=True
        )

        unread_shared_bundle = self.create_bundle(
            {
                "name": "Unread and shared",
                "search": "match",
                "filter_unread": "yes",
                "filter_shared": "yes",
            }
        )
        read_bundle = self.create_bundle(
            {"name": "Read", "search": "match", "filter_unread": "no"}
        )

        response = self.client.get(
            reverse("linkding:bookmarks.index") + f"?bundle={unread_shared_bundle}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertVisibleBookmarks(response, [unread_shared])
        self.assertInvisibleBookmarks(
            response, [unread_unshared, read_shared, read_unshared, other]
        )

        response = self.client.get(
            reverse("linkding:bookmarks.index") + f"?bundle={read_bundle}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertVisibleBookmarks(response, [read_shared, read_unshared])
        self.assertInvisibleBookmarks(response, [unread_shared, unread_unshared, other])


class BundleFilterStateFormTestCase(
    LinkdingApiTestCase, BookmarkFactoryMixin, BookmarkListTestMixin
):
    def setUp(self) -> None:
        user = self.get_or_create_test_user()
        user.profile.enable_sharing = True
        user.profile.save()
        self.authenticate()
        self.client.force_login(user)

    def find_select(self, soup, label_text: str):
        labels = [
            label
            for label in soup.select("label")
            if label.get_text(strip=True) == label_text
        ]
        self.assertEqual(len(labels), 1, f"No single label '{label_text}' found")
        label = labels[0]
        if label.get("for"):
            select = soup.find(id=label["for"])
        else:
            select = label.find("select")
        self.assertIsNotNone(select, f"No control labelled '{label_text}' found")
        self.assertEqual(select.name, "select")
        return select

    def option_texts(self, select) -> list:
        return [option.get_text(strip=True) for option in select.select("option")]

    def option_value(self, select, option_text: str) -> str:
        options = [
            option
            for option in select.select("option")
            if option.get_text(strip=True) == option_text
        ]
        self.assertEqual(len(options), 1, f"No single option '{option_text}' found")
        return options[0].get("value")

    def selected_option_text(self, select) -> str:
        selected = [
            option for option in select.select("option") if option.has_attr("selected")
        ]
        if not selected:
            # Browsers select the first option when none is marked selected
            selected = select.select("option")[:1]
        self.assertEqual(len(selected), 1)
        return selected[0].get_text(strip=True)

    def get_form_soup(self, url: str):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return self.make_soup(response.content.decode())

    def get_bundle_by_name(self, name: str) -> dict:
        response = self.get(
            reverse("linkding:bundle-list"), expected_status_code=status.HTTP_200_OK
        )
        matches = [b for b in response.data["results"] if b["name"] == name]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def assertFilterState(self, data: dict, filter_unread: str, filter_shared: str):
        self.assertIn("filter_unread", data)
        self.assertIn("filter_shared", data)
        self.assertEqual(data["filter_unread"], filter_unread)
        self.assertEqual(data["filter_shared"], filter_shared)

    def test_new_bundle_form_shows_and_stores_reading_and_sharing_state(self):
        unread_shared = self.setup_bookmark(
            title="match unread shared", unread=True, shared=True
        )
        unread_unshared = self.setup_bookmark(
            title="match unread unshared", unread=True, shared=False
        )
        read_shared = self.setup_bookmark(
            title="match read shared", unread=False, shared=True
        )

        soup = self.get_form_soup(reverse("linkding:bundles.new"))
        reading = self.find_select(soup, "Reading State")
        sharing = self.find_select(soup, "Sharing State")
        self.assertEqual(self.option_texts(reading), ["All", "Unread", "Read"])
        self.assertEqual(self.option_texts(sharing), ["All", "Shared", "Unshared"])
        self.assertEqual(self.selected_option_text(reading), "All")
        self.assertEqual(self.selected_option_text(sharing), "All")

        response = self.client.post(
            reverse("linkding:bundles.new"),
            {
                "name": "Unread shared bundle",
                "search": "match",
                "any_tags": "",
                "all_tags": "",
                "excluded_tags": "",
                reading["name"]: self.option_value(reading, "Unread"),
                sharing["name"]: self.option_value(sharing, "Shared"),
            },
        )
        self.assertRedirects(response, reverse("linkding:bundles.index"))

        bundle = self.get_bundle_by_name("Unread shared bundle")
        self.assertFilterState(bundle, "yes", "yes")

        soup = self.get_form_soup(
            reverse("linkding:bundles.edit", kwargs={"bundle_id": bundle["id"]})
        )
        self.assertEqual(
            self.selected_option_text(self.find_select(soup, "Reading State")),
            "Unread",
        )
        self.assertEqual(
            self.selected_option_text(self.find_select(soup, "Sharing State")),
            "Shared",
        )

        response = self.client.get(
            reverse("linkding:bookmarks.index") + f"?bundle={bundle['id']}"
        )
        self.assertVisibleBookmarks(response, [unread_shared])
        self.assertInvisibleBookmarks(response, [unread_unshared, read_shared])

    def test_edit_bundle_form_stores_reading_and_sharing_state(self):
        unread_unshared = self.setup_bookmark(
            title="match unread unshared", unread=True, shared=False
        )
        read_shared = self.setup_bookmark(
            title="match read shared", unread=False, shared=True
        )
        read_unshared = self.setup_bookmark(
            title="match read unshared", unread=False, shared=False
        )
        bundle = self.setup_bundle(name="Existing bundle", search="match")
        edit_url = reverse("linkding:bundles.edit", kwargs={"bundle_id": bundle.id})

        soup = self.get_form_soup(edit_url)
        reading = self.find_select(soup, "Reading State")
        sharing = self.find_select(soup, "Sharing State")
        self.assertEqual(self.option_texts(reading), ["All", "Unread", "Read"])
        self.assertEqual(self.option_texts(sharing), ["All", "Shared", "Unshared"])
        self.assertEqual(self.selected_option_text(reading), "All")
        self.assertEqual(self.selected_option_text(sharing), "All")

        response = self.client.post(
            edit_url,
            {
                "name": "Existing bundle",
                "search": "match",
                "any_tags": "",
                "all_tags": "",
                "excluded_tags": "",
                reading["name"]: self.option_value(reading, "Read"),
                sharing["name"]: self.option_value(sharing, "Unshared"),
            },
        )
        self.assertRedirects(response, reverse("linkding:bundles.index"))

        self.assertFilterState(self.get_bundle_by_name("Existing bundle"), "no", "no")
        self.assertEqual(BookmarkBundle.objects.filter(owner=self.user).count(), 1)

        response = self.client.get(
            reverse("linkding:bookmarks.index") + f"?bundle={bundle.id}"
        )
        self.assertVisibleBookmarks(response, [read_unshared])
        self.assertInvisibleBookmarks(response, [unread_unshared, read_shared])
