"""Explicit tool allow-list.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

This dict is the authorization control. A name that is not a key here
cannot be called — the same allow-listing principle as the Week 1
AI Boundary Matrix. scripts/review_defect.py is intentionally absent.
"""

from __future__ import annotations

from . import check_course_load, create_defect_report

ALLOW_LIST = {
    "check_course_load": {
        "module": check_course_load,
        "required": ("year_of_study", "units_requested"),
        "side_effect": False,
        "authorization": "unconditional read",
    },
    "create_defect_report": {
        "module": create_defect_report,
        "required": ("story_id", "rule_id", "title", "description", "severity"),
        "side_effect": True,
        "authorization": "draft pending_review only",
    },
}


def is_allowed(name: str) -> bool:
    return name in ALLOW_LIST
