#!/usr/bin/env python3
"""Lint and export the human-readable Markdown test cases.

The cases are the half of a sign-off a person reads: one file per case under
``testcases/<area>/TC-<area>-<nnn>.md``, written by hand, parsed here. The
skeleton, the metadata keys and the export column names live in
``plugins/signoff/formats.md`` and are not restated in this file's prose; this
script is their implementation.

Usage:
    cases.py check <testcases dir> [--tiles .qa/tiles.json] [--tests .qa/tests.json]
    cases.py export --format azure-csv|gherkin|markdown <testcases dir> --out <path>
                    [--tiles ...] [--tests ...]
    cases.py index <testcases dir>

``check`` prints one line per finding, ``path:line rule: reason``, then a
summary line; exit 1 when anything was found, 0 when clean, 2 when an input
could not be read (fail closed: a tiles file that will not parse is never a
pass). ``export`` runs the same check first and refuses (exit 1) when it would
fail, so a broken case never reaches a test-management tool. ``index`` prints
the JSON another script consumes.

The rules ``check`` can report, all of them:

    title-line          the first non-blank line is not `# <id>: <title>`
    bad-id              the id in the title line is not TC-<area>-<nnn>
    title-id-mismatch   that id is not the file's name
    duplicate-id        two files carry the same id
    missing-metadata    a key of the fixed metadata list is absent
    metadata-order      the keys are present but not in the fixed order
    duplicate-metadata  a key appears twice
    unknown-metadata    a key that is not one of the six
    stray-metadata      a line in the metadata block that is not `- key: value`
    bad-area            `area` is not the kebab-case identifier formats.md fixes
    bad-value           a value outside its allowed set, or empty where required
    automated-mismatch  `automated` is set on a case that is not automated,
                        or empty on one that is
    missing-section     `## Preconditions` or `## Steps` is absent
    section-order       `## Steps` comes before `## Preconditions`
    empty-preconditions the preconditions list has no items (`- none` is one)
    empty-steps         the steps table has no data row
    bad-table           the steps table has no `|---|` separator row
    bad-table-row       a step row has fewer than three columns
    empty-cell          a step's action or expected is empty
    too-large           the file is past the size a written case can be
    unreadable          the file could not be read at all
    dangling-tile       (--tiles) a tile the case names is not in tiles.json
    dangling-test       (--tests) an `automated` id is not in tests.json
    test-tile-mismatch  (--tests) that test claims none of the case's tiles
    uncased-tile        (--tiles) a covered tile no case names, reported once
                        per tile at `<tiles path>:0`

Standard library only, no network: this reads and writes files and nothing else.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

# --------------------------------------------------------------------------- constants

# Case files are named for their id; a testcases tree holds README and other
# prose beside them, so the name is what makes a file a case.
CASE_PREFIX = "TC-"
CASE_SUFFIX = ".md"

# A case is prose a person wrote. A quarter of a megabyte is far past the
# largest real one, and refusing to read past it keeps a generated or hostile
# file from turning the lint into a memory problem.
MAX_CASE_BYTES = 256 * 1024

# A tiles.json or tests.json for an application of any size stays well under
# this; the cap is here so an unbounded file cannot be read into memory.
MAX_JSON_BYTES = 8 * 1024 * 1024

# The metadata list in the order formats.md fixes. The order is part of the
# skeleton so a reader, and a diff, always find a field in the same place.
META_KEYS = ("area", "tiles", "role", "priority", "status", "automated")

# The two enumerations formats.md closes. `planned` is a case written before
# the behaviour exists; `manual` is one nobody intends to automate.
STATUSES = ("automated", "manual", "planned")
PRIORITIES = ("high", "medium", "low")

# The status whose cases must exist for every tile: a tile a test covers with
# no case behind it is coverage nobody can read.
COVERED_STATUS = "covered"

# `TC-<area>-<nnn>`: kebab-case area, exactly three digits. Three is what
# formats.md writes; a thousandth case in one area is a sign to split the area,
# not to widen the id.
ID_RE = re.compile(r"^TC-([a-z][a-z0-9-]*)-([0-9]{3})$")
# The area on its own, the pattern formats.md gives under "Identifiers" and
# the one the id above embeds. Checked before an area is joined into any path:
# an export writes `<area>.feature`, so an area holding a separator or `..`
# would place a file the writer did not name.
AREA_RE = re.compile(r"^[a-z][a-z0-9-]*$")
TITLE_RE = re.compile(r"^#[ \t]+([^:]+):[ \t]*(.*\S)[ \t]*$")
META_RE = re.compile(r"^-[ \t]+([A-Za-z][A-Za-z0-9_-]*)[ \t]*:[ \t]*(.*?)[ \t]*$")
BULLET_RE = re.compile(r"^-[ \t]+(.*?)[ \t]*$")
HEADING_RE = re.compile(r"^##[ \t]+(.*?)[ \t]*$")
# A Markdown table separator row: dashes, colons, pipes and spaces only.
SEPARATOR_RE = re.compile(r"^\|[-:| \t]+\|[ \t]*$")
# A cell boundary is an unescaped pipe, so a step may contain `\|`.
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")

# The word `- none` stands for an empty preconditions list, so that an empty
# section is always a mistake and never a shrug.
NO_PRECONDITIONS = "none"

# The two section headings of the skeleton, in the order they must appear.
SECTION_PRECONDITIONS = "Preconditions"
SECTION_STEPS = "Steps"

# The nine columns Azure Test Plans documents for a test-case import, in order.
# Written exactly, header included: the importer matches on these names.
AZURE_HEADER = [
    "ID",
    "Work Item Type",
    "Title",
    "Test Step",
    "Step Action",
    "Step Expected",
    "Area Path",
    "Assigned To",
    "State",
]
AZURE_WORK_ITEM_TYPE = "Test Case"
# Azure's initial state for a newly imported case; `ID` and `Assigned To` are
# left empty so the import creates the item and leaves ownership to a person.
AZURE_STATE = "Design"

# The CSV is committed and diffed like source, so it gets LF endings rather
# than the CRLF the csv module writes by default; Azure accepts either.
CSV_LINETERMINATOR = "\n"

EXPORT_FORMATS = ("azure-csv", "gherkin", "markdown")

# `json` does not keep line numbers and a whole-file problem has no line, so
# every such finding points at line 0 - the shape the other scripts use.
NO_LINE = 0


# --------------------------------------------------------------------------- model

# CLAUDE.md: a string that originates in a scanned repository is sanitized,
# length-capped and origin-marked before it reaches a report, because the
# report is untrusted input to the model that reads it. A newline inside an
# id is how a fake `## Coverage` heading gets into a Markdown report.
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
# An id or an area: past the longest real one, still one line on a screen.
ID_CHARS = 120
# A title or a path, which legitimately runs longer than an id.
TEXT_CHARS = 200
# The cut is marked, so a value that was truncated never reads as a whole one.
CUT_MARK = "\u2026"


def _safe(value, cap=ID_CHARS):
    """One repository-born string, fit to print: control characters and
    newlines replaced, length capped, the cut marked."""
    text = CONTROL_RE.sub("?", str(value))
    return text if len(text) <= cap else text[: cap - 1] + CUT_MARK


class Finding(object):
    """One lint result: a place, a rule name, and a reason in one line."""

    def __init__(self, path, line, rule, reason):
        # The path holds a file name from the tree and the reason interpolates
        # the case's own values, so both are cleaned here rather than at each
        # of the twenty places a finding is raised.
        self.path = _safe(path, TEXT_CHARS)
        self.line = line
        self.rule = rule
        self.reason = _safe(reason, TEXT_CHARS)

    def key(self):
        return (self.path, self.line, self.rule, self.reason)

    def __str__(self):
        return "%s:%d %s: %s" % (self.path, self.line, self.rule, self.reason)


class Case(object):
    """A parsed case file. Fields are empty when the skeleton was broken."""

    def __init__(self, path):
        self.path = path
        self.id = ""
        self.id_area = ""
        self.title = ""
        self.area = ""
        self.role = ""
        self.priority = ""
        self.status = ""
        self.tiles = []
        self.automated = []
        self.preconditions = []
        self.steps = []
        self.title_line = 1
        self.meta_lines = {}

    def line_of(self, key):
        """The line a metadata key sits on, falling back to the title line."""
        return self.meta_lines.get(key, self.title_line)


# --------------------------------------------------------------------------- parsing


def _split_row(line):
    """Cells of a Markdown table row, outer pipes dropped, `\\|` unescaped."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [c.strip().replace("\\|", "|") for c in CELL_SPLIT_RE.split(stripped)]


def _split_list(value):
    """A comma-separated metadata value as a list, empties dropped."""
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_case(path):
    """Parse one case file. Returns (Case, [Finding]); the Case is always usable."""
    case = Case(path)
    findings = []

    def add(line, rule, reason):
        findings.append(Finding(path, line, rule, reason))

    try:
        if os.path.getsize(path) > MAX_CASE_BYTES:
            add(0, "too-large", "case file is larger than %d bytes" % MAX_CASE_BYTES)
            return case, findings
        # errors="replace" so one stray byte is a lint finding at worst, never
        # a crash that hides every other case in the tree.
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        add(0, "unreadable", "case file could not be read (%s)" % exc.__class__.__name__)
        return case, findings

    first = None
    for i, line in enumerate(lines):
        if line.strip():
            first = i
            break
    if first is None:
        add(1, "title-line", "case file is empty")
        return case, findings

    case.title_line = first + 1
    match = TITLE_RE.match(lines[first])
    stem = os.path.basename(path)[: -len(CASE_SUFFIX)]
    if not match:
        add(case.title_line, "title-line", "first line is not `# TC-<area>-<nnn>: <title>`")
    else:
        case.id = _safe(match.group(1).strip())
        case.title = _safe(match.group(2).strip(), TEXT_CHARS)
        id_match = ID_RE.match(case.id)
        if not id_match:
            add(case.title_line, "bad-id", "id `%s` is not TC-<area>-<nnn>" % case.id)
        else:
            case.id_area = id_match.group(1)
        if case.id != stem:
            add(
                case.title_line,
                "title-id-mismatch",
                "title id `%s` is not the file name `%s`" % (case.id, stem),
            )

    # The metadata block runs from the title line to the first `## ` heading.
    end = len(lines)
    for i in range(first + 1, len(lines)):
        if HEADING_RE.match(lines[i]):
            end = i
            break

    values = {}
    order = []
    for i in range(first + 1, end):
        line = lines[i]
        if not line.strip():
            continue
        meta = META_RE.match(line)
        if not meta:
            add(i + 1, "stray-metadata", "line before the first section is not `- <key>: <value>`")
            continue
        key = meta.group(1).lower()
        value = meta.group(2).strip()
        if key not in META_KEYS:
            add(i + 1, "unknown-metadata", "`%s` is not one of the six metadata keys" % key)
            continue
        if key in values:
            add(i + 1, "duplicate-metadata", "`%s` is given twice" % key)
            continue
        values[key] = value
        case.meta_lines[key] = i + 1
        order.append(key)

    for key in META_KEYS:
        if key not in values:
            add(case.title_line, "missing-metadata", "the `%s` line is missing" % key)
    expected = [key for key in META_KEYS if key in values]
    if order != expected:
        add(
            case.line_of(order[0]) if order else case.title_line,
            "metadata-order",
            "the metadata keys are not in the order %s" % ", ".join(META_KEYS),
        )

    case.area = _safe(values.get("area", ""))
    case.role = _safe(values.get("role", ""))
    case.priority = _safe(values.get("priority", ""))
    case.status = _safe(values.get("status", ""))
    case.tiles = [_safe(tile) for tile in _split_list(values.get("tiles", ""))]
    # A test id is a path joined to a title, so it is capped as one.
    case.automated = [_safe(t, TEXT_CHARS) for t in _split_list(values.get("automated", ""))]

    if "area" in values:
        if not case.area:
            add(case.line_of("area"), "bad-value", "`area` is empty")
        elif not AREA_RE.match(case.area):
            # One finding, not two: an area this malformed cannot also be
            # judged against the id, and the id mismatch would only repeat it.
            add(case.line_of("area"), "bad-area", "`area` is not kebab-case (`%s`)" % AREA_RE.pattern)
        elif case.id_area and case.area != case.id_area:
            add(
                case.line_of("area"),
                "bad-value",
                "`area` is `%s` but the id says `%s`" % (case.area, case.id_area),
            )
    if "tiles" in values and not case.tiles:
        add(case.line_of("tiles"), "bad-value", "`tiles` names no tile")
    if "role" in values and not case.role:
        add(case.line_of("role"), "bad-value", "`role` is empty")
    if "priority" in values and case.priority not in PRIORITIES:
        add(
            case.line_of("priority"),
            "bad-value",
            "`priority` is `%s`, not one of %s" % (case.priority, ", ".join(PRIORITIES)),
        )
    if "status" in values and case.status not in STATUSES:
        add(
            case.line_of("status"),
            "bad-value",
            "`status` is `%s`, not one of %s" % (case.status, ", ".join(STATUSES)),
        )
    if "status" in values and "automated" in values and case.status in STATUSES:
        if case.status == "automated" and not case.automated:
            add(
                case.line_of("automated"),
                "automated-mismatch",
                "`status` is automated but `automated` names no test",
            )
        if case.status != "automated" and case.automated:
            add(
                case.line_of("automated"),
                "automated-mismatch",
                "`automated` names a test but `status` is `%s`" % case.status,
            )

    # Sections: name, first line index, line index after the heading block.
    heads = []
    for i in range(end, len(lines)):
        heading = HEADING_RE.match(lines[i])
        if heading:
            heads.append((heading.group(1).strip(), i))

    def region(index):
        start = heads[index][1] + 1
        stop = heads[index + 1][1] if index + 1 < len(heads) else len(lines)
        return start, stop

    names = [name for name, _ in heads]
    pre_at = names.index(SECTION_PRECONDITIONS) if SECTION_PRECONDITIONS in names else None
    steps_at = names.index(SECTION_STEPS) if SECTION_STEPS in names else None
    if pre_at is None:
        add(case.title_line, "missing-section", "`## %s` is missing" % SECTION_PRECONDITIONS)
    if steps_at is None:
        add(case.title_line, "missing-section", "`## %s` is missing" % SECTION_STEPS)
    if pre_at is not None and steps_at is not None and steps_at < pre_at:
        add(
            heads[steps_at][1] + 1,
            "section-order",
            "`## %s` comes before `## %s`" % (SECTION_STEPS, SECTION_PRECONDITIONS),
        )

    if pre_at is not None:
        start, stop = region(pre_at)
        items = []
        for i in range(start, stop):
            bullet = BULLET_RE.match(lines[i])
            if bullet and bullet.group(1):
                items.append(bullet.group(1))
        if not items:
            add(
                heads[pre_at][1] + 1,
                "empty-preconditions",
                "no preconditions listed (write `- %s` when there are none)" % NO_PRECONDITIONS,
            )
        elif len(items) == 1 and items[0].strip().lower() == NO_PRECONDITIONS:
            case.preconditions = []
        else:
            case.preconditions = items

    if steps_at is not None:
        start, stop = region(steps_at)
        # The first table only: the header row, the separator row, then the
        # consecutive `|` rows, ending at the first line that is not one.
        # Anything after it is the free prose formats.md allows, and a data
        # table written in that prose is prose, not two more steps.
        table = []
        index = start
        while index < stop and not lines[index].strip().startswith("|"):
            index += 1
        while index < stop and lines[index].strip().startswith("|"):
            table.append((index, lines[index]))
            index += 1
        if not table:
            add(heads[steps_at][1] + 1, "empty-steps", "no steps table")
        else:
            if len(table) > 1 and SEPARATOR_RE.match(table[1][1].strip()):
                rows = table[2:]
            else:
                add(table[0][0] + 1, "bad-table", "the steps table has no `|---|` separator row")
                rows = table[1:]
            if not rows:
                add(heads[steps_at][1] + 1, "empty-steps", "the steps table has no rows")
            for i, line in rows:
                cells = _split_row(line)
                if len(cells) < 3:
                    add(i + 1, "bad-table-row", "step row has fewer than three columns")
                    continue
                action, expected_text = cells[1], cells[2]
                # cells[0] is the step's own number: read by people, ignored
                # here because every export renumbers the steps from 1.
                if not action or not expected_text:
                    add(i + 1, "empty-cell", "step row has an empty action or expected")
                    continue
                case.steps.append((action, expected_text))

    return case, findings


def collect_cases(root):
    """Every TC-*.md under root, sorted by path. Returns (cases, findings)."""
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if name.startswith(CASE_PREFIX) and name.endswith(CASE_SUFFIX):
                paths.append(os.path.join(dirpath, name))
    paths.sort()

    cases = []
    findings = []
    seen = {}
    for path in paths:
        case, case_findings = parse_case(path)
        findings.extend(case_findings)
        if case.id:
            if case.id in seen:
                findings.append(
                    Finding(
                        path,
                        case.title_line,
                        "duplicate-id",
                        "id `%s` is already used by %s" % (case.id, seen[case.id]),
                    )
                )
            else:
                seen[case.id] = path
        cases.append(case)
    return cases, findings


# --------------------------------------------------------------------------- cross-file checks


def _fail(path, rule, reason):
    """Refuse an input, in the `path:line rule: reason` shape every script in
    this plugin uses. `json` keeps no line numbers, so the line is always 0."""
    sys.stderr.write("cases.py: %s:%d %s: %s\n" % (path, NO_LINE, rule, reason))
    raise SystemExit(2)


def _load_json(path):
    """Read a JSON file or exit 2: an input that will not parse is not a pass."""
    try:
        if os.path.getsize(path) > MAX_JSON_BYTES:
            _fail(path, "too-large", "file is larger than %d bytes" % MAX_JSON_BYTES)
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except SystemExit:
        raise
    except (OSError, ValueError) as exc:
        _fail(path, "unreadable", "file could not be read (%s)" % exc.__class__.__name__)


def check_tiles(cases, tiles_path):
    """Findings that need .qa/tiles.json: dangling tiles and uncased tiles."""
    data = _load_json(tiles_path)
    tiles = data.get("tiles") if isinstance(data, dict) else None
    if not isinstance(tiles, list):
        _fail(tiles_path, "malformed", "no `tiles` list")
    known = {}
    for tile in tiles:
        if isinstance(tile, dict) and tile.get("id"):
            known[_safe(tile["id"])] = _safe(tile.get("status", ""))

    findings = []
    named = set()
    for case in cases:
        for tile in case.tiles:
            named.add(tile)
            if tile not in known:
                findings.append(
                    Finding(
                        case.path,
                        case.line_of("tiles"),
                        "dangling-tile",
                        "tile `%s` is not in %s" % (tile, tiles_path),
                    )
                )
    for tile_id in sorted(known):
        if known[tile_id] == COVERED_STATUS and tile_id not in named:
            # Reported against the tiles file, once per tile: no case file is
            # to blame for a tile nobody wrote a case for.
            findings.append(
                Finding(tiles_path, 0, "uncased-tile", "covered tile `%s` is named by no case" % tile_id)
            )
    return findings


def check_tests(cases, tests_path):
    """Findings that need .qa/tests.json: dangling and mismatched automated ids."""
    data = _load_json(tests_path)
    tests = data.get("tests") if isinstance(data, dict) else None
    if not isinstance(tests, list):
        _fail(tests_path, "malformed", "no `tests` list")
    claims = {}
    for test in tests:
        if isinstance(test, dict) and test.get("id"):
            claims[_safe(test["id"], TEXT_CHARS)] = {_safe(t) for t in test.get("tiles") or []}

    findings = []
    for case in cases:
        for test_id in case.automated:
            line = case.line_of("automated")
            if test_id not in claims:
                findings.append(
                    Finding(
                        case.path, line, "dangling-test", "test `%s` is not in %s" % (test_id, tests_path)
                    )
                )
            elif not (claims[test_id] & set(case.tiles)):
                findings.append(
                    Finding(
                        case.path,
                        line,
                        "test-tile-mismatch",
                        "test `%s` claims none of the case's tiles" % test_id,
                    )
                )
    return findings


def run_check(root, tiles_path, tests_path):
    """Every finding for a tree, sorted. Returns (cases, findings)."""
    cases, findings = collect_cases(root)
    if tiles_path:
        findings.extend(check_tiles(cases, tiles_path))
    if tests_path:
        findings.extend(check_tests(cases, tests_path))
    findings.sort(key=lambda finding: finding.key())
    return cases, findings


# --------------------------------------------------------------------------- exports


def _escape_cell(text):
    """A value going into a Markdown table cell."""
    return text.replace("|", "\\|")


def _by_area(cases):
    """Cases grouped by area, areas and cases both in id order."""
    groups = {}
    for case in sorted(cases, key=lambda case: case.id):
        groups.setdefault(case.area or case.id_area, []).append(case)
    return groups


def export_azure(cases, out):
    """One CSV, one row per step, the header formats.md fixes."""
    _ensure_parent(out)
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator=CSV_LINETERMINATOR)
        writer.writerow(AZURE_HEADER)
        for case in sorted(cases, key=lambda case: case.id):
            title = "%s: %s" % (case.id, case.title)
            for number, (action, expected) in enumerate(case.steps, 1):
                # Title is repeated on every row: Azure groups the rows of one
                # work item by it, so a blank would start a second item.
                writer.writerow(
                    ["", AZURE_WORK_ITEM_TYPE, title, number, action, expected, case.area, "", AZURE_STATE]
                )
    return [out]


def export_gherkin(cases, out):
    """One <area>.feature per area, one Scenario per case."""
    written = []
    if not os.path.isdir(out):
        os.makedirs(out, exist_ok=True)
    for area, group in sorted(_by_area(cases).items()):
        # `check` refuses a bad area before an export ever runs; this is the
        # second lock on the same door, because the area becomes a file name.
        if not AREA_RE.match(area or ""):
            _fail(out, "bad-area", "an area is not %s and was not written" % AREA_RE.pattern)
        lines = ["Feature: %s" % area, ""]
        for case in group:
            lines.append("  Scenario: %s %s" % (case.id, case.title))
            for index, precondition in enumerate(case.preconditions):
                lines.append("    %s %s" % ("Given" if index == 0 else "And", precondition))
            for index, (action, expected) in enumerate(case.steps):
                lines.append("    %s %s" % ("When" if index == 0 else "And", action))
                lines.append("    %s %s" % ("Then" if index == 0 else "And", expected))
            lines.append("")
        path = os.path.join(out, "%s.feature" % area)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines).rstrip("\n") + "\n")
        written.append(path)
    return written


def export_markdown(cases, out):
    """The index: a table per area of every case."""
    _ensure_parent(out)
    lines = ["# Test cases", ""]
    for area, group in sorted(_by_area(cases).items()):
        lines.append("## %s" % area)
        lines.append("")
        lines.append("| ID | Title | Status | Priority | Tiles | Automated |")
        lines.append("|---|---|---|---|---|---|")
        for case in group:
            lines.append(
                "| %s | %s | %s | %s | %s | %s |"
                % (
                    case.id,
                    _escape_cell(case.title),
                    case.status,
                    case.priority,
                    _escape_cell(", ".join(case.tiles)),
                    _escape_cell(", ".join(case.automated)),
                )
            )
        lines.append("")
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).rstrip("\n") + "\n")
    return [out]


def _ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def index_of(cases):
    """The shape another script consumes: one object per case, id order."""
    return [
        {
            "id": case.id,
            "area": case.area or case.id_area,
            "tiles": case.tiles,
            "status": case.status,
            "automated": case.automated,
            "path": _safe(case.path, TEXT_CHARS),
        }
        for case in sorted(cases, key=lambda case: case.id)
    ]


# --------------------------------------------------------------------------- cli


def _parser():
    parser = argparse.ArgumentParser(prog="cases.py", description="Lint and export the Markdown test cases.")
    subs = parser.add_subparsers(dest="command")

    check = subs.add_parser("check", help="lint every TC-*.md under a directory")
    check.add_argument("root", metavar="TESTCASES_DIR")
    check.add_argument("--tiles", metavar="PATH", help="also check tiles against .qa/tiles.json")
    check.add_argument("--tests", metavar="PATH", help="also check automated ids against .qa/tests.json")

    export = subs.add_parser("export", help="write the cases out for another tool")
    export.add_argument("root", metavar="TESTCASES_DIR")
    export.add_argument("--format", dest="fmt", required=True, choices=EXPORT_FORMATS)
    export.add_argument(
        "--out",
        required=True,
        metavar="PATH",
        help="a file for azure-csv and markdown, a directory for gherkin",
    )
    export.add_argument("--tiles", metavar="PATH")
    export.add_argument("--tests", metavar="PATH")

    index = subs.add_parser("index", help="print the cases as JSON")
    index.add_argument("root", metavar="TESTCASES_DIR")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if not args.command:
        _parser().print_help()
        return 2
    if not os.path.isdir(args.root):
        sys.stderr.write("cases.py: %s:%d unreadable: not a directory\n" % (args.root, NO_LINE))
        return 2

    if args.command == "index":
        cases, _ = collect_cases(args.root)
        print(json.dumps(index_of(cases), indent=2, sort_keys=True))
        return 0

    cases, findings = run_check(args.root, args.tiles, args.tests)

    if args.command == "check":
        for finding in findings:
            print(finding)
        print("%d cases checked, %d findings" % (len(cases), len(findings)))
        return 1 if findings else 0

    if findings:
        for finding in findings:
            print(finding)
        print("export refused: %d findings; fix the cases first" % len(findings))
        return 1
    if args.fmt == "azure-csv":
        written = export_azure(cases, args.out)
    elif args.fmt == "gherkin":
        written = export_gherkin(cases, args.out)
    else:
        written = export_markdown(cases, args.out)
    for path in written:
        print("wrote %s" % path)
    print("%d cases exported as %s" % (len(cases), args.fmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
