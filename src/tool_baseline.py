"""
UniFlow QA Agent — Week 4 tool-calling baseline.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

Manual JSON-dispatch (same family as baseline.py / rag_baseline.py):
    request -> generate() -> if status == tool_call
        -> allow-list + schema check -> real Python tool
        -> generate() again with the tool result -> final answer
    -> one trace for the whole loop

Native provider function-calling is considered, not used: it would add
separate Gemini functionDeclarations and Groq tools schemas on top of
the two provider paths already in llm_client.py. The JSON contract is
provider-agnostic, matching Week 1 §5's allow-listed agentic loop.

Usage:
    python src/tool_baseline.py --request "Is 6 units allowed in Year 3?"
    python src/tool_baseline.py --request "Draft a defect for US-08 / R-04 over-load"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from llm_client import generate  # noqa: E402
from tools.dispatch import dispatch  # noqa: E402
from tools.registry import ALLOW_LIST  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "evidence" / "traces" / "tools"

VALID_STATUSES = {
    "tool_call",
    "ok",
    "partial",
    "insufficient_context",
    "out_of_scope",
    "refused",
}
MAX_TOOL_ROUNDS = 2

SYSTEM = (
    "You are the UniFlow QA Agent.\n"
    "You check approved academic-management rules and draft defect reports.\n"
    "You do not approve defects, modify student records, access secrets, "
    "or call any tool that is not listed below.\n"
    "When a question needs a rule check or a durable draft, request a tool "
    "instead of inventing the result in prose.\n"
    "You respond with a single JSON object and nothing else."
)

OUTPUT_CONTRACT = """
## Approved tools

check_course_load — read-only R-04 check.
  arguments: {"year_of_study": <int 1-4>, "units_requested": <int >= 0>}
  Do not invent a student id for this tool; it has none.

create_defect_report — write a pending_review draft only.
  arguments: {"story_id": "US-NN", "rule_id": "R-NN", "title": "...",
              "description": "...", "severity": "low"|"medium"|"high"}
  Never include a status field. Never mark a defect approved or rejected.
  Approving a defect is a human-only action outside your tools.

## Output contract

If you need a tool, return:

{{
  "status": "tool_call",
  "tool": "check_course_load",
  "arguments": {{"year_of_study": 3, "units_requested": 6}},
  "answer": "",
  "reason": ""
}}

If you can finish, return:

{{
  "status": "ok",
  "tool": "",
  "arguments": {{}},
  "answer": "Plain-language answer.",
  "reason": ""
}}

"status" must be one of:
  - "tool_call"             you need an approved tool before answering
  - "ok"                    you can answer from the tool result or the request
  - "partial"               you can only answer part of the request
  - "insufficient_context"  needed facts are missing; do not guess them
  - "out_of_scope"          excluded workflow (admissions, grading, fees, ...)
  - "refused"               prohibited action (approve a defect, change records,
                             deploy, access secrets, call an unlisted tool)

Never guess a missing tool argument. Never call a tool that is not listed.
"""


def parse_and_validate(raw: str) -> dict:
    report = {
        "json_parsed_first_try": False,
        "json_parsed_after_repair": False,
        "schema_errors": [],
        "parsed": None,
    }
    stripped = (raw or "").strip()
    if not stripped:
        report["schema_errors"].append("empty response")
        return report

    try:
        report["parsed"] = json.loads(stripped)
        report["json_parsed_first_try"] = True
    except json.JSONDecodeError:
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.MULTILINE).strip()
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if match:
            try:
                report["parsed"] = json.loads(match.group(0))
                report["json_parsed_after_repair"] = True
            except json.JSONDecodeError as exc:
                report["schema_errors"].append(f"unparseable JSON: {exc}")
                return report
        else:
            report["schema_errors"].append("no JSON object found in response")
            return report

    obj = report["parsed"]
    if not isinstance(obj, dict):
        report["schema_errors"].append("top level is not an object")
        return report
    if obj.get("status") not in VALID_STATUSES:
        report["schema_errors"].append(f"invalid or missing status: {obj.get('status')!r}")
    if obj.get("status") == "tool_call":
        if obj.get("tool") not in ALLOW_LIST:
            report["schema_errors"].append(f"tool_call names a non-allow-listed tool: {obj.get('tool')!r}")
        if not isinstance(obj.get("arguments", {}), dict):
            report["schema_errors"].append("arguments is not an object")
    return report


def _user_prompt(request: str, prior_steps: list[dict]) -> str:
    body = f"## Request\n{request}\n"
    if prior_steps:
        body += "\n## Tool results so far\n"
        body += json.dumps(prior_steps, indent=2)
        body += (
            "\n\nUse the tool results. If you have enough to answer, return a "
            "final status (not tool_call) unless another *approved* tool is "
            "still required. If a tool returned tool_error, explain that "
            "failure — do not invent a successful result.\n"
        )
    return body + OUTPUT_CONTRACT + "\n## Instruction\nReturn only the JSON object.\n"


def handle_request(
    request: str,
    *,
    tag: str = "",
    scripted_turns: list[dict] | None = None,
    inject: str | None = None,
    defects_dir: Path | None = None,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> dict:
    """Run the tool loop. scripted_turns replace generate() for offline eval."""
    steps: list[dict] = []
    tool_results: list[dict] = []
    final = None
    last_validation = None
    model_calls = []

    for round_i in range(max_rounds + 1):
        user = _user_prompt(request, tool_results)
        if scripted_turns is not None:
            if round_i >= len(scripted_turns):
                last_validation = {
                    "json_parsed_first_try": False,
                    "json_parsed_after_repair": False,
                    "schema_errors": ["no further scripted turn"],
                    "parsed": None,
                }
                raw = ""
                model_record = {"scripted": True, "error": "no further scripted turn", "text": ""}
            else:
                raw = json.dumps(scripted_turns[round_i])
                last_validation = parse_and_validate(raw)
                model_record = {
                    "scripted": True,
                    "text": raw,
                    "error": None,
                    "latency_ms": 0,
                }
        else:
            resp = generate(user=user, system=SYSTEM)
            raw = resp.text
            last_validation = parse_and_validate(raw)
            model_record = resp.to_dict()

        model_calls.append(model_record)
        parsed = last_validation["parsed"]
        steps.append({
            "round": round_i,
            "kind": "model",
            "parsed": parsed,
            "schema_errors": list(last_validation["schema_errors"]),
        })

        if parsed is None:
            break

        if parsed.get("status") != "tool_call":
            final = parsed
            break

        # Allow-list + schema live in dispatch, even if parse flagged the name.
        result = dispatch(
            str(parsed.get("tool") or ""),
            parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {},
            inject=inject if round_i == 0 else None,
            defects_dir=defects_dir,
        )
        record = {
            "tool": parsed.get("tool"),
            "arguments": parsed.get("arguments"),
            "result": result,
        }
        tool_results.append(record)
        steps.append({"round": round_i, "kind": "dispatch", **record})

        if round_i >= max_rounds - 1:
            # Force a stop: do not silently drop the last tool result.
            if scripted_turns is not None and round_i + 1 < len(scripted_turns):
                continue
            if scripted_turns is None:
                continue
            final = {
                "status": "partial",
                "tool": "",
                "arguments": {},
                "answer": "Stopped at the tool-round limit after the last tool result.",
                "reason": "max_tool_rounds reached",
            }
            break

    trace = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": request,
        "tag": tag,
        "steps": steps,
        "tool_results": tool_results,
        "model_calls": model_calls,
        "validation": {k: v for k, v in (last_validation or {}).items() if k != "parsed"},
        "parsed_output": final,
    }

    TRACES.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", request.lower())[:40].strip("-")
    path = TRACES / f"{stamp}_{slug}{('_' + tag) if tag else ''}.json"
    path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    trace["_trace_path"] = str(path.relative_to(ROOT))
    return trace


def main() -> None:
    ap = argparse.ArgumentParser(description="UniFlow QA Agent — tool-calling baseline")
    ap.add_argument("--request", required=True)
    args = ap.parse_args()

    trace = handle_request(args.request)
    parsed = trace["parsed_output"] or {}
    last_model = trace["model_calls"][-1] if trace["model_calls"] else {}
    if last_model.get("error"):
        print(f"MODEL ERROR: {last_model['error']}")
        print(f"trace: {trace['_trace_path']}")
        return

    tools_used = [s["tool"] for s in trace["tool_results"]]
    print(f"status={parsed.get('status', '?')}  tools={tools_used}")
    if parsed.get("answer"):
        print(f"answer: {parsed['answer']}")
    if parsed.get("reason"):
        print(f"reason: {parsed['reason']}")
    for item in trace["tool_results"]:
        print(f"  {item['tool']} -> {item['result']}")
    print(f"trace: {trace['_trace_path']}")


if __name__ == "__main__":
    main()
