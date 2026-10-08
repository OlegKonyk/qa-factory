You write the human-readable test cases a person approves, one Markdown file per automated test,
in a fixed skeleton that a linter checks. Read the test files named below, then write the cases.
Do not modify anything in the repository.

## The ticket

{ticket_json}

## The tests to describe

{tests_listing}

## The skeleton (exact; the linter is strict)

```markdown
# TC-{area}-001: <title in plain words, what the test proves>

- area: {area}
- tiles: {area}.<flow>.<rule-slug>
- role: <who performs it, e.g. user>
- priority: high | medium | low
- status: automated
- automated: <test id>

## Preconditions

- <one line each, or `- none`>

## Steps

| # | Action | Expected |
|---|--------|----------|
| 1 | <what the person or the test does> | <what must be observed> |
```

Rules:
- One file per test, numbered 001, 002, ... in the order of the listing, saved as
  `{out_dir}/{area}/TC-{area}-<nnn>.md`. Create the folder.
- `automated` is the test id exactly as listed: `<file>::<Class>::<test_name>`.
- `tiles` is one identifier of the form `{area}.<flow>.<rule-slug>` (lower case, hyphens), the
  behaviour the test proves, e.g. `{area}.sort.modified-ascending`.
- Steps describe the public surface (the request made, the control used, the order seen), never
  code. Expected cells say what is observed, with the concrete values the test uses.
- Plain English a product owner can read; no code identifiers except the test id.

Respond only through the structured output: the list of files written.
