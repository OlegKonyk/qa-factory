# Step 1 frame needs a person

Kind: clarify

Who: Oleg

Question: Frame cannot hand 'Add sort by modification date option' to a test writer as is:
- missing from the ticket: Blocks AC1 and AC2b: the API parameter value for the new sort (for example `modified_asc` and `modified_desc`) is not named, and neither is the parameter, which is presumably the existing `sort`.
- missing from the ticket: Blocks AC2a: the UI labels for the new options (for example 'Modified ↑' and 'Modified ↓') are not stated.
- missing from the ticket: Blocks AC1 and AC3: which direction is ascending and which is descending is not stated, though it is presumably analogous to the existing added options.
- missing from the ticket: Blocks AC2b: it is not stated whether the API list responses change, for example by exposing a date_modified field, or whether that field already exists in them.

Accepted answers:

- `proceed`: go on with the ticket as Frame read it
- `clarify` (with "ticket"): replace the ticket's description, contract or acceptance_criteria with the fields given, then frame the clarified ticket again
- `decline`: the step fails with the note as its reason

Context:

```json
{
  "missing_contract": [
    "Blocks AC1 and AC2b: the API parameter value for the new sort (for example `modified_asc` and `modified_desc`) is not named, and neither is the parameter, which is presumably the existing `sort`.",
    "Blocks AC2a: the UI labels for the new options (for example 'Modified \u2191' and 'Modified \u2193') are not stated.",
    "Blocks AC1 and AC3: which direction is ascending and which is descending is not stated, though it is presumably analogous to the existing added options.",
    "Blocks AC2b: it is not stated whether the API list responses change, for example by exposing a date_modified field, or whether that field already exists in them."
  ],
  "untestable": [],
  "ambiguities": [
    "AC1: 'modification date' is presumed to be the date_modified field, but the ticket does not say so. Editing, archiving, tagging, or marking a bookmark read or unread may or may not update it.",
    "AC1: the ticket does not say how ties are ordered when two bookmarks have the same modification time.",
    "AC2: 'wherever bookmarks can be sorted' is not enumerated. It could cover the active, archived, shared and bundle views, the user preferences/settings default sort, and the API list endpoints. It is unclear whether the tags page sort is in scope (its sort is by tag, not bookmark).",
    "AC2: it is unclear whether the option can be saved as the user's default sort preference.",
    "AC2: it is unclear whether the API option applies to the bookmarks, archived and shared endpoints, or only some.",
    "AC3: 'works as expected' is undefined. It could mean the same ordering as active bookmarks, or that archiving itself counts as a modification and moves the bookmark.",
    "AC3: it is unclear whether the sort should persist when the user moves between the active and archived views.",
    "Behaviour for an invalid sort value is not stated for the API (ignore, fall back to the default, or error). The ticket does not say whether this should change."
  ],
  "frame": "/Users/oleg/dev/qa-factory-wt/gates/.artifacts/runs-proof2/linkding-sort-by-modified-vague/frame/frame.json"
}
```

Answer by writing /Users/oleg/dev/qa-factory-wt/gates/.artifacts/runs-proof2/linkding-sort-by-modified-vague/answer.json (`by` is required), for example:

```json
{"decision": "proceed", "by": "Oleg", "note": ""}
```
