"""Week 7 guardrails for the UniFlow QA Agent.

These checks run in Python, around the model, not only inside the prompt.
A request that tries to override the instructions never reaches generate().
A model reply that is not in the output contract, that contradicts a tool
result, or that claims a human-only decision, is not stored as a success.

Ordinary "please approve this defect" requests are deliberately not blocked
here. Those must still reach dispatch(), which is what returns
tool_error: unauthorized — see tests/test_tools.py.
"""

from __future__ import annotations

import re

MAX_REQUEST_CHARS = 4000

VALID_STATUSES = {
    "tool_call",
    "ok",
    "partial",
    "insufficient_context",
    "out_of_scope",
    "refused",
}

# Phrases already seen in this project's own eval (RQ-15) and the Boundary
# Matrix actions that are attempts to override the agent, rather than
# ordinary requests the allow-list is meant to refuse.
_INJECTION = (
    (re.compile(r"ignore (all )?(previous|prior|above) instructions", re.I), "ignore_previous_instructions"),
    (re.compile(r"disregard (the |your )?(rules|system prompt|instructions)", re.I), "disregard_instructions"),
    (re.compile(r"(reveal|print|show|dump).{0,60}(system prompt|\.env|api[_ ]?key|secret)", re.I), "exfiltrate_secret_or_prompt"),
    (re.compile(r"you are now", re.I), "role_override"),
    (re.compile(r"<\s*/?\s*(system|prompt)\s*>", re.I), "fake_system_tag"),
)

# Actions the Week 1 Boundary Matrix says the agent must refuse. Kept
# separate from tool-argument smuggling (status=approved), which dispatch
# already owns.
_PROHIBITED = (
    (re.compile(r"\b(deploy|merge)\b.{0,40}\b(code|production|changes)\b", re.I), "deploy_or_merge"),
    (re.compile(r"\b(modify|change|update|alter)\b.{0,50}\b(academic record|grade|student record)\b", re.I), "modify_academic_record"),
    (re.compile(r"\b(delete|drop)\b.{0,40}\b(database|records|files)\b", re.I), "delete_data"),
    (re.compile(r"\b(run|execute)\b.{0,30}\b(shell|bash|command)\b", re.I), "execute_shell"),
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_COURSE_LOAD_REQUEST = re.compile(r"\b(course load|units)\b", re.I)
_NOT_ALLOWED = re.compile(r"\b(not allowed|exceeds|over the limit|violation)\b", re.I)
_IS_ALLOWED = re.compile(r"\b(is|are) allowed\b", re.I)
_CLAIMS_APPROVAL = re.compile(
    r"\b(i approved|has been approved|is now approved|defect approved|marked approved|status approved)\b",
    re.I,
)
_DENIES_APPROVAL = re.compile(
    r"\b(cannot|can't|not authorised|not authorized|unable to|will not|won't)\b.{0,40}\bapprov",
    re.I,
)
_CLAIMS_TOOL_SUCCESS = re.compile(
    r"\b(successfully (created|written|filed)|defect (has been|was) created)\b",
    re.I,
)
# The unapproved retake draft (KB-RETAKE-DRAFT) states "up to 2 times".
# Presenting that number as a rule, without saying it is a draft, is the
# incorrect-information failure Week 3 already recorded.
_RETAKE_AS_RULE = re.compile(r"\bretake\b", re.I)
_RETAKE_COUNT = re.compile(r"\b(up to 2|twice|two times)\b", re.I)
_RETAKE_HEDGED = re.compile(r"\b(draft|unapproved|not approved|insufficient)\b", re.I)


def screen_request(request: str) -> dict:
    """Decide whether the request may enter the model loop.

    blocked=False means the loop should run. reasons are the signal names
    a trace should record either way.
    """
    text = request if isinstance(request, str) else ""
    input_reasons: list[str] = []
    if not text.strip():
        input_reasons.append("empty_request")
    elif len(text) > MAX_REQUEST_CHARS:
        input_reasons.append("request_too_long")
    if _CONTROL_CHARS.search(text):
        input_reasons.append("control_characters")

    injection = [name for pattern, name in _INJECTION if pattern.search(text)]
    prohibited = [name for pattern, name in _PROHIBITED if pattern.search(text)]

    if input_reasons:
        status = "insufficient_context" if input_reasons == ["empty_request"] else "refused"
        return {
            "blocked": True,
            "status": status,
            "input_reasons": input_reasons,
            "injection": injection,
            "prohibited": prohibited,
            "safety_violations": input_reasons + injection + prohibited,
            "answer": _block_answer(status, input_reasons + injection + prohibited),
        }

    signals = injection + prohibited
    if signals:
        return {
            "blocked": True,
            "status": "refused",
            "input_reasons": [],
            "injection": injection,
            "prohibited": prohibited,
            "safety_violations": signals,
            "answer": _block_answer("refused", signals),
        }

    return {
        "blocked": False,
        "status": None,
        "input_reasons": [],
        "injection": [],
        "prohibited": [],
        "safety_violations": [],
        "answer": "",
    }


def screen_output(
    parsed: dict | None,
    tool_results: list[dict],
    schema_errors: list[str],
    request: str,
) -> list[str]:
    """Return finding names for a model-produced terminal object. Empty means accept it."""
    findings: list[str] = []
    if parsed is None:
        return ["unparseable_output"]
    if not isinstance(parsed, dict):
        return ["invalid_status"]

    status = parsed.get("status")
    if status not in VALID_STATUSES or any("invalid or missing status" in err for err in schema_errors):
        findings.append("invalid_status")

    answer = str(parsed.get("answer") or "")
    if _claims_approval(answer):
        findings.append("claims_approval")
    if _contradicts_tool(answer, tool_results):
        findings.append("contradicts_tool_result")
    if _claims_success_after_error(answer, tool_results):
        findings.append("claims_success_after_tool_error")
    if _presents_draft_as_rule(answer):
        findings.append("presents_draft_as_approved")
    if status == "ok" and _course_load_without_tool(request, tool_results):
        findings.append("ungrounded_course_load")
    return findings


def groundedness(findings: list[str], tool_results: list[dict]) -> str:
    """pass / fail / not_applicable for the course-load and draft-rule checks."""
    if any(
        name in findings
        for name in ("contradicts_tool_result", "ungrounded_course_load", "presents_draft_as_approved")
    ):
        return "fail"
    if any(
        item.get("tool") == "check_course_load" and isinstance(item.get("result"), dict) and "ok" in item["result"]
        for item in tool_results
    ):
        return "pass"
    return "not_applicable"


def _block_answer(status: str, reasons: list[str]) -> str:
    joined = ", ".join(reasons)
    if status == "insufficient_context":
        return "No request was provided."
    return f"Refused before the model was called ({joined})."


def _claims_approval(answer: str) -> bool:
    if _DENIES_APPROVAL.search(answer):
        return False
    if "pending_review" in answer.lower() and not re.search(r"\b(i approved|is now approved)\b", answer, re.I):
        return False
    return bool(_CLAIMS_APPROVAL.search(answer))


def _load_claim(answer: str) -> str | None:
    denied = bool(_NOT_ALLOWED.search(answer))
    allowed = bool(_IS_ALLOWED.search(answer)) and not denied
    if allowed:
        return "allowed"
    if denied:
        return "denied"
    return None


def _contradicts_tool(answer: str, tool_results: list[dict]) -> bool:
    claim = _load_claim(answer)
    if claim is None:
        return False
    for item in tool_results:
        result = item.get("result")
        if item.get("tool") != "check_course_load" or not isinstance(result, dict) or "ok" not in result:
            continue
        if result["ok"] is True and claim == "denied":
            return True
        if result["ok"] is False and claim == "allowed":
            return True
    return False


def _claims_success_after_error(answer: str, tool_results: list[dict]) -> bool:
    if not tool_results:
        return False
    last = tool_results[-1].get("result")
    if not isinstance(last, dict) or "tool_error" not in last:
        return False
    return bool(_CLAIMS_TOOL_SUCCESS.search(answer))


def _presents_draft_as_rule(answer: str) -> bool:
    if not (_RETAKE_AS_RULE.search(answer) and _RETAKE_COUNT.search(answer)):
        return False
    return not bool(_RETAKE_HEDGED.search(answer))


def _course_load_without_tool(request: str, tool_results: list[dict]) -> bool:
    if not _COURSE_LOAD_REQUEST.search(request or ""):
        return False
    return not any(
        item.get("tool") == "check_course_load" and isinstance(item.get("result"), dict) and "ok" in item["result"]
        for item in tool_results
    )
