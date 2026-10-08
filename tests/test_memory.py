"""Offline tests for Week 6 persistent memory (case history). No API key required.

    python -m pytest tests/test_memory.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from memory.case_history import find_prior_defect, forget, remember_defect  # noqa: E402


def test_unseen_violation_returns_none(tmp_path):
    store = tmp_path / "case_history.json"
    assert find_prior_defect("R-04", "US-08", store=store) is None


def test_remember_then_find(tmp_path):
    store = tmp_path / "case_history.json"
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    found = find_prior_defect("R-04", "US-08", store=store)
    assert found["defect_id"] == "DEF-1"
    assert found["times_seen"] == 1
    assert found["first_seen"] == found["last_seen"]


def test_remembering_the_same_violation_again_increments_times_seen(tmp_path):
    store = tmp_path / "case_history.json"
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    found = find_prior_defect("R-04", "US-08", store=store)
    assert found["times_seen"] == 2
    # first_seen must not move once set, even though last_seen can.
    assert found["first_seen"] <= found["last_seen"]


def test_different_rule_story_pairs_are_independent(tmp_path):
    store = tmp_path / "case_history.json"
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    assert find_prior_defect("R-07", "US-09", store=store) is None
    assert find_prior_defect("R-04", "US-08", store=store) is not None


def test_forget_removes_the_entry(tmp_path):
    store = tmp_path / "case_history.json"
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    assert forget("R-04", "US-08", store=store) is True
    assert find_prior_defect("R-04", "US-08", store=store) is None


def test_forget_on_unknown_entry_returns_false(tmp_path):
    store = tmp_path / "case_history.json"
    assert forget("R-04", "US-08", store=store) is False


def test_corrupt_store_is_treated_as_empty_not_a_crash(tmp_path):
    store = tmp_path / "case_history.json"
    store.write_text("{not valid json", encoding="utf-8")
    assert find_prior_defect("R-04", "US-08", store=store) is None
    # The next successful write repairs the file rather than preserving the corruption.
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    assert json.loads(store.read_text(encoding="utf-8"))


def test_store_is_plain_json_keyed_by_rule_and_story(tmp_path):
    """The on-disk shape must stay a simple, human-readable file — this is
    what docs/Week6_Memory_Design.md promises a reviewer can open directly.
    """
    store = tmp_path / "case_history.json"
    remember_defect("R-04", "US-08", "DEF-1", "evidence/defects/DEF-1.json", store=store)
    on_disk = json.loads(store.read_text(encoding="utf-8"))
    assert on_disk == {
        "R-04:US-08": {
            "rule_id": "R-04",
            "story_id": "US-08",
            "defect_id": "DEF-1",
            "path": "evidence/defects/DEF-1.json",
            "first_seen": on_disk["R-04:US-08"]["first_seen"],
            "last_seen": on_disk["R-04:US-08"]["last_seen"],
            "times_seen": 1,
        }
    }
