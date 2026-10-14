# Step 1 frame needs a person

Kind: clarify

Who: Oleg

Question: Frame cannot hand 'Add sort by modification date option' to a test writer as is:
- missing from the ticket: AC3: the DOM locator of the sort dropdown on the bookmark list page is not stated by the ticket or the code before the change. The code renders a form field from BookmarkSearchForm.sort in search.html, but the select's id/name in the rendered page is not given, and neither is whether the option value attribute equals 'modified_asc'/'modified_desc'.
- missing from the ticket: AC3: the URL query behaviour after selecting an option (whether the page reloads with ?sort=modified_asc) is not stated.
- missing from the ticket: AC4: the route for the archived UI list page is not named in the ticket. It is only implied by 'archived bookmarks list'.
- missing from the ticket: AC1/AC2: the way to set distinct date_modified values for fixtures is not stated. The ticket does not say whether the API response exposes a date_modified field to assert on, so tests may need to check order by bookmark IDs or titles.

Accepted answers:

- `proceed`: go on with the ticket as Frame read it
- `clarify` (with "ticket"): replace the ticket's description, contract or acceptance_criteria with the fields given, then frame the clarified ticket again
- `decline`: the step fails with the note as its reason

Context:

```json
{
  "missing_contract": [
    "AC3: the DOM locator of the sort dropdown on the bookmark list page is not stated by the ticket or the code before the change. The code renders a form field from BookmarkSearchForm.sort in search.html, but the select's id/name in the rendered page is not given, and neither is whether the option value attribute equals 'modified_asc'/'modified_desc'.",
    "AC3: the URL query behaviour after selecting an option (whether the page reloads with ?sort=modified_asc) is not stated.",
    "AC4: the route for the archived UI list page is not named in the ticket. It is only implied by 'archived bookmarks list'.",
    "AC1/AC2: the way to set distinct date_modified values for fixtures is not stated. The ticket does not say whether the API response exposes a date_modified field to assert on, so tests may need to check order by bookmark IDs or titles."
  ],
  "untestable": [],
  "ambiguities": [
    "AC1/AC2: ordering of bookmarks with equal date_modified (e.g. bulk-created) is unspecified, so tests must use distinct timestamps.",
    "AC1/AC2: it is unclear whether the API orders by the date_modified field only, or whether it also changes when a bookmark is edited. A test needs to set date_modified explicitly or edit a bookmark to move it.",
    "AC3: 'selecting one reorders the list' does not say whether this is checked through the URL (?sort=modified_asc after the dropdown submits) or only through the visible order. It also does not say whether the selected option stays selected after reload.",
    "AC4: 'the archived bookmarks list and its API' does not say whether the archived UI page has its own dropdown. In the current code the sort preference form is shared across list views through search.html.",
    "The ticket does not mention the shared bookmarks list (/api/bookmarks/shared/, the shared UI page). Existing sort options apply there, and 'wherever the existing sort options are' suggests it is included, but it is not in the criteria.",
    "The ticket does not say whether the sort choice persists in user profile preferences (BookmarkSearch preferences include 'sort'), nor whether the profile settings need the new options.",
    "AC5: 'unknown' is not defined for the UI. The page may ignore an invalid sort query value or may fail form validation, since the form's ChoiceField only accepts listed choices."
  ],
  "frame": "/Users/oleg/dev/qa-factory-wt/gates/.artifacts/runs/linkding-sort-by-modified-vague/frame/frame.json"
}
```

Answer by writing /Users/oleg/dev/qa-factory-wt/gates/.artifacts/runs/linkding-sort-by-modified-vague/answer.json (`by` is required), for example:

```json
{"decision": "proceed", "by": "Oleg", "note": ""}
```
