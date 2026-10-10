import json

import pytest

from factory.rounds import DEFAULT_CAPS, CapReached, Ledger, caps_for


def test_caps_merge_order():
    caps = caps_for({"caps": {"advice": 5, "extra": 1}}, {"caps": {"advice": 1, "usd": 4.0}})
    assert caps == {"writer_rounds": 3, "advice": 5, "usd": 4.0, "extra": 1}
    assert caps_for({}, {}) == DEFAULT_CAPS


def test_add_writes_and_resumes(tmp_path):
    ledger = Ledger(tmp_path)
    assert not ledger.path.exists()
    ledger.add("verify", "repair", 0.25, model="m", round=1)
    ledger.add("verify", "advice", 0.5)
    data = json.loads(ledger.path.read_text())
    assert data["spent_usd"] == 0.75 and len(data["entries"]) == 2
    assert data["entries"][0]["kind"] == "repair" and data["caps"] == DEFAULT_CAPS
    again = Ledger(tmp_path)
    assert len(again.entries) == 2 and again.spent() == 0.75


def test_counts_and_left(tmp_path):
    ledger = Ledger(tmp_path, {"writer_rounds": 2, "advice": 1, "usd": 10.0})
    ledger.add("v", "write", 0.1)
    assert ledger.rounds_left() == 2
    ledger.add("v", "repair", 0.1)
    ledger.add("v", "review_fix", 0.1)
    ledger.add("v", "guided", 0.1)
    assert ledger.count("repair", "guided") == 2
    assert ledger.rounds_left() == 0 and ledger.advice_left() == 1
    ledger.add("v", "advice", 0.1)
    assert ledger.advice_left() == 0
    assert ledger.summary() == {
        "caps": ledger.caps,
        "spent_usd": 0.5,
        "writer_rounds_used": 3,
        "advice_used": 1,
        "calls": 5,
    }


def test_budget_for_min_and_cap(tmp_path):
    ledger = Ledger(tmp_path, {"writer_rounds": 3, "advice": 2, "usd": 5.0})
    assert ledger.budget_for(3.0) == 3.0
    ledger.add("v", "write", 3.0)
    assert ledger.budget_for(3.0) == 2.0
    ledger.add("v", "write", 1.6)
    with pytest.raises(CapReached, match="spend cap reached: 4.60 of 5.00 USD"):
        ledger.budget_for(3.0)


def test_constructor_caps_replace_file_caps(tmp_path):
    Ledger(tmp_path, {"writer_rounds": 1, "advice": 1, "usd": 1.0}).add("v", "write", 0.1)
    assert Ledger(tmp_path).caps["writer_rounds"] == 1
    assert Ledger(tmp_path, {"writer_rounds": 9, "advice": 1, "usd": 1.0}).caps["writer_rounds"] == 9


def test_two_ledgers_on_one_folder_keep_each_others_calls(tmp_path):
    held = Ledger(tmp_path)  # Review holds this one while Verify's fix round writes through another
    held.add("review", "review", 0.5)
    other = Ledger(tmp_path)
    other.add("verify", "review_fix", 4.0)
    other.add("verify", "advice", 3.0)
    held.add("review", "review", 0.5)
    again = Ledger(tmp_path)
    assert [e["kind"] for e in again.entries] == ["review", "review_fix", "advice", "review"]
    assert held.count("review_fix") == 1
    assert held.spent() == 8.0


def test_budget_for_can_ask_for_a_larger_minimum(tmp_path):
    ledger = Ledger(tmp_path, {"usd": 8.0})
    ledger.add("verify", "write", 7.25)
    assert ledger.budget_for(3.0) == 0.75
    with pytest.raises(CapReached):
        ledger.budget_for(3.0, minimum=1.5)
