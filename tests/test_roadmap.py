"""The roadmap state command: string fixtures for the parser and one test on the real docs/roadmap.md."""

import io
import json
from pathlib import Path

import pytest

from factory import __main__ as cli
from factory import roadmap
from factory.roadmap import STATES, RoadmapError

REAL = Path(__file__).resolve().parent.parent / "docs" / "roadmap.md"

SAMPLE = """# Roadmap

## Where the factory is

Prose. State: not an item.

## Now: first

### 1. Plan it

State: planned

Body text.

### 2. Build it

State: in progress, since 2026-10-15

## Next: second

### 3. Ship it

State: done 2026-10-13, #19, 5.69 USD measured (6 estimated)

## Later: third

### 4. Maybe

State: dropped 2026-10-14, superseded by item 3
"""


def test_parses_three_groups_and_four_states():
    items = roadmap.parse(SAMPLE)
    assert [(i.number, i.title, i.group, i.state) for i in items] == [
        (1, "Plan it", "now", "planned"),
        (2, "Build it", "now", "in progress"),
        (3, "Ship it", "next", "done"),
        (4, "Maybe", "later", "dropped"),
    ]
    assert [i.note for i in items] == [
        "",
        "since 2026-10-15",
        "2026-10-13, #19, 5.69 USD measured (6 estimated)",
        "2026-10-14, superseded by item 3",
    ]


def test_item_without_state_names_the_item():
    with pytest.raises(RoadmapError, match=r"item 1 \(Plan it\).*no State"):
        roadmap.parse("## Now\n\n### 1. Plan it\n\nText.\n")


def test_unknown_state_word_raises():
    with pytest.raises(RoadmapError, match="unknown state"):
        roadmap.parse("## Now\n\n### 1. Plan it\n\nState: started\n")


def test_item_before_any_group_raises():
    with pytest.raises(RoadmapError, match=r"item 1 \(Plan it\).*outside"):
        roadmap.parse("### 1. Plan it\n\nState: planned\n")


def test_item_after_a_non_group_heading_is_outside_a_group():
    with pytest.raises(RoadmapError, match="outside"):
        roadmap.parse("## Now\n\n## Notes\n\n### 1. Plan it\n\nState: planned\n")


@pytest.mark.parametrize("numbers", [(1, 2, 4), (2, 1)])
def test_numbers_must_run_one_to_n_in_order(numbers):
    text = "## Now\n\n" + "".join(f"### {n}. T{n}\n\nState: planned\n\n" for n in numbers)
    with pytest.raises(RoadmapError, match="1\\.\\."):
        roadmap.parse(text)


def test_state_after_the_next_group_heading_does_not_count():
    text = "## Now\n\n### 1. Plan it\n\n## Next\n\nState: planned\n"
    with pytest.raises(RoadmapError, match=r"item 1 \(Plan it\).*no State"):
        roadmap.parse(text)


def test_render_has_header_one_line_per_item_and_counts_without_zeros():
    lines = roadmap.render(roadmap.parse(SAMPLE)).splitlines()
    assert lines[0].split() == ["#", "group", "state", "title", "note"]
    assert len(lines) == 1 + 4 + 1
    assert lines[2].startswith("2  now    in progress  Build it")
    assert lines[-1] == "4 items: 1 planned, 1 in progress, 1 done, 1 dropped"
    only_planned = roadmap.render(roadmap.parse("## Now\n\n### 1. A\n\nState: planned\n"))
    assert only_planned.splitlines()[-1] == "1 items: 1 planned"


def test_main_json_prints_a_list_of_items(tmp_path):
    path = tmp_path / "roadmap.md"
    path.write_text(SAMPLE)
    buf = io.StringIO()
    assert roadmap.main(str(path), as_json=True, out=buf) == 0
    data = json.loads(buf.getvalue())
    assert len(data) == 4
    assert set(data[0]) == {"number", "title", "group", "state", "note"}


def test_main_on_a_bad_file_returns_1(tmp_path):
    path = tmp_path / "roadmap.md"
    path.write_text("## Now\n\n### 1. Plan it\n")
    buf = io.StringIO()
    assert roadmap.main(str(path), out=buf) == 1
    assert buf.getvalue().startswith("roadmap: ")


def test_real_roadmap_loads():
    items = roadmap.load(REAL)
    assert [i.number for i in items] == list(range(1, 11))
    assert [i.group for i in items] == ["now"] * 4 + ["next"] * 2 + ["later"] * 4
    assert all(i.state in STATES for i in items)


def test_cli_prints_the_table(tmp_path, capsys):
    path = tmp_path / "roadmap.md"
    path.write_text(SAMPLE)
    assert cli.main(["roadmap", "--path", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Build it" in out and out.splitlines()[-1].startswith("4 items:")
