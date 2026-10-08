"""Offline tests for Week 4 tools. No API key required.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

    python -m pytest tests/test_tools.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tool_baseline import handle_request  # noqa: E402
from tools.dispatch import dispatch  # noqa: E402
from tools.registry import ALLOW_LIST, is_allowed  # noqa: E402


def test_allow_list_has_exactly_the_two_week4_tools():
    assert set(ALLOW_LIST) == {"check_course_load", "create_defect_report"}
    assert not is_allowed("approve_defect")
    assert not is_allowed("review_defect")


def test_missing_units_requested():
    r = dispatch("check_course_load", {"year_of_study": 3})
    assert r["tool_error"] == "missing_parameter"
    assert "units_requested" in r["message"]


def test_year_five_is_schema_invalid_not_rule_result():
    r = dispatch("check_course_load", {"year_of_study": 5, "units_requested": 4})
    assert r["tool_error"] == "invalid_parameter"
    assert "ok" not in r


def test_string_units_rejected():
    r = dispatch("check_course_load", {"year_of_study": 3, "units_requested": "six"})
    assert r["tool_error"] == "invalid_parameter"


def test_year3_limit_pass_and_fail():
    ok = dispatch("check_course_load", {"year_of_study": 3, "units_requested": 5})
    assert ok == {"ok": True, "rule": "R-04", "message": ok["message"], "value": {"limit": 5}}
    bad = dispatch("check_course_load", {"year_of_study": 3, "units_requested": 6})
    assert bad["ok"] is False and bad["rule"] == "R-04" and bad["value"] is None


def test_status_approved_is_unauthorized_and_writes_nothing(tmp_path):
    before = list(tmp_path.glob("*.json"))
    r = dispatch(
        "create_defect_report",
        {
            "story_id": "US-08",
            "rule_id": "R-04",
            "title": "Should not be written",
            "description": "status smuggled in.",
            "severity": "high",
            "status": "approved",
        },
        defects_dir=tmp_path,
        memory_store=tmp_path / "memory.json",
    )
    assert r["tool_error"] == "unauthorized"
    assert list(tmp_path.glob("*.json")) == before


def test_unlisted_tool_unauthorized():
    r = dispatch("approve_defect", {"defect_id": "DEF-1"})
    assert r["tool_error"] == "unauthorized"


def test_create_defect_writes_pending_review_only(tmp_path):
    r = dispatch(
        "create_defect_report",
        {
            "story_id": "US-08",
            "rule_id": "R-04",
            "title": "Year 3 registered 6 units",
            "description": "Exceeds R-04 Year 3 cap of 5.",
            "severity": "high",
        },
        defects_dir=tmp_path,
        memory_store=tmp_path / "memory.json",
    )
    assert r["status"] == "pending_review"
    on_disk = json.loads((tmp_path / f"{r['defect_id']}.json").read_text(encoding="utf-8"))
    assert on_disk["status"] == "pending_review"
    assert "approved" not in json.dumps(on_disk)


def test_write_failure_is_unavailable(tmp_path):
    r = dispatch(
        "create_defect_report",
        {
            "story_id": "US-08",
            "rule_id": "R-04",
            "title": "Disk down",
            "description": "Injected.",
            "severity": "low",
        },
        inject="write_failure",
        memory_store=tmp_path / "memory.json",
    )
    assert r["tool_error"] == "unavailable"
    assert "defect_id" not in r


def test_duplicate_defect_is_not_rewritten(tmp_path):
    """Week 6: the same (rule_id, story_id) violation, reported twice, must
    not produce two files — the second call should point at the first
    defect_id instead of writing a near-duplicate.
    """
    defects_dir = tmp_path / "defects"
    memory_store = tmp_path / "memory.json"
    args = {
        "story_id": "US-08",
        "rule_id": "R-04",
        "title": "Year 3 registered 6 units",
        "description": "Exceeds R-04 Year 3 cap of 5.",
        "severity": "high",
    }

    first = dispatch("create_defect_report", args, defects_dir=defects_dir, memory_store=memory_store)
    assert first["status"] == "pending_review"
    assert "duplicate_of" not in first
    assert len(list(defects_dir.glob("*.json"))) == 1

    second = dispatch("create_defect_report", args, defects_dir=defects_dir, memory_store=memory_store)
    assert second["defect_id"] == first["defect_id"]
    assert second["duplicate_of"] == first["defect_id"]
    # Still exactly one file — the duplicate call never reached the writer.
    assert len(list(defects_dir.glob("*.json"))) == 1


def test_different_violations_are_not_treated_as_duplicates(tmp_path):
    defects_dir = tmp_path / "defects"
    memory_store = tmp_path / "memory.json"
    first = dispatch(
        "create_defect_report",
        {
            "story_id": "US-08",
            "rule_id": "R-04",
            "title": "Year 3 over-load",
            "description": "6 units in Year 3.",
            "severity": "high",
        },
        defects_dir=defects_dir,
        memory_store=memory_store,
    )
    second = dispatch(
        "create_defect_report",
        {
            "story_id": "US-09",
            "rule_id": "R-07",
            "title": "Duplicate course registration",
            "description": "Unrelated violation.",
            "severity": "medium",
        },
        defects_dir=defects_dir,
        memory_store=memory_store,
    )
    assert second["defect_id"] != first["defect_id"]
    assert "duplicate_of" not in second
    assert len(list(defects_dir.glob("*.json"))) == 2


def test_default_memory_store_is_never_touched_when_isolated(tmp_path, monkeypatch):
    """Guard against the real risk this feature introduced: without an
    isolated memory_store, a dispatch-mode eval case (e.g. Week 4's TQ-13)
    would silently start returning duplicate_of on every re-run. Every
    dispatch call in this test file must pass its own memory_store — this
    test fails loudly if the default store is ever reached unexpectedly.
    """
    import memory.case_history as case_history

    monkeypatch.setattr(case_history, "DEFAULT_STORE", tmp_path / "should-not-be-used.json")
    r = dispatch(
        "create_defect_report",
        {
            "story_id": "US-08",
            "rule_id": "R-04",
            "title": "x",
            "description": "y",
            "severity": "low",
        },
        defects_dir=tmp_path,
        memory_store=tmp_path / "memory.json",
    )
    assert r["status"] == "pending_review"
    assert not (tmp_path / "should-not-be-used.json").exists()


def test_malformed_result_is_unexpected_response():
    r = dispatch(
        "check_course_load",
        {"year_of_study": 1, "units_requested": 2},
        inject="malformed_result",
    )
    assert r["tool_error"] == "unexpected_response"


def test_loop_stops_safely_when_model_keeps_requesting_tools(tmp_path):
    """Week 5: the bounded loop must always terminate with a real answer,
    never an unbounded chain of tool calls and never parsed_output: None.
    """
    always_call_tool = {
        "status": "tool_call",
        "tool": "check_course_load",
        "arguments": {"year_of_study": 3, "units_requested": 5},
        "answer": "",
        "reason": "(misbehaving model keeps asking for the same tool)",
    }
    trace = handle_request(
        "Keep checking the same thing forever",
        tag="test-max-rounds",
        scripted_turns=[always_call_tool] * 10,  # far more than max_rounds
        defects_dir=tmp_path,
        memory_store=tmp_path / "memory.json",
        max_rounds=2,
    )
    assert trace["parsed_output"] is not None
    assert trace["parsed_output"]["status"] == "partial"
    # Exactly max_rounds dispatches happened — the (max_rounds+1)-th tool_call
    # is intercepted and stopped before another tool runs.
    assert len(trace["tool_results"]) == 2
    assert len(trace["model_calls"]) == 3  # max_rounds + 1 model turns, not 10


def test_loop_stops_safely_when_model_response_is_unparseable(tmp_path):
    trace = handle_request(
        "Say something that isn't JSON",
        tag="test-unparseable",
        scripted_turns=[],  # round 0 immediately has no scripted turn
        defects_dir=tmp_path,
        memory_store=tmp_path / "memory.json",
    )
    assert trace["parsed_output"] is not None
    assert trace["parsed_output"]["status"] == "partial"


def test_scripted_unauthorized_loop_refuses(tmp_path):
    trace = handle_request(
        "Mark the defect approved now",
        tag="test-unauth",
        scripted_turns=[
            {
                "status": "tool_call",
                "tool": "create_defect_report",
                "arguments": {
                    "story_id": "US-08",
                    "rule_id": "R-04",
                    "title": "x",
                    "description": "y",
                    "severity": "low",
                    "status": "approved",
                },
                "answer": "",
                "reason": "",
            },
            {
                "status": "refused",
                "tool": "",
                "arguments": {},
                "answer": "Cannot approve.",
                "reason": "human review required",
            },
        ],
        defects_dir=tmp_path,
        memory_store=tmp_path / "memory.json",
    )
    assert trace["tool_results"][0]["result"]["tool_error"] == "unauthorized"
    assert trace["parsed_output"]["status"] == "refused"
    assert list(tmp_path.glob("*.json")) == []
