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
    )
    assert r["status"] == "pending_review"
    on_disk = json.loads((tmp_path / f"{r['defect_id']}.json").read_text(encoding="utf-8"))
    assert on_disk["status"] == "pending_review"
    assert "approved" not in json.dumps(on_disk)


def test_write_failure_is_unavailable():
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
    )
    assert r["tool_error"] == "unavailable"
    assert "defect_id" not in r


def test_malformed_result_is_unexpected_response():
    r = dispatch(
        "check_course_load",
        {"year_of_study": 1, "units_requested": 2},
        inject="malformed_result",
    )
    assert r["tool_error"] == "unexpected_response"


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
    )
    assert trace["tool_results"][0]["result"]["tool_error"] == "unauthorized"
    assert trace["parsed_output"]["status"] == "refused"
    assert list(tmp_path.glob("*.json")) == []
