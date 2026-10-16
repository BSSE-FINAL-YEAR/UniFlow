"""
UniFlow QA Agent — Week 4 tool-calling baseline, extended in Week 5 into a
bounded agent loop.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration);
Week 5 bounded-autonomy changes: Swale Sebabe Abdu (AI/Agent Lead).

Manual JSON-dispatch (same family as baseline.py / rag_baseline.py), now
framed explicitly as the Week 5 agent loop:

    Sense (request + tool results so far) -> Plan/Decide (generate())
        -> if status == tool_call: Act (allow-list + schema check -> real
           Python tool) -> Observe (tool result fed back as the next
           round's Sense input) -> Re-plan (loop)
        -> else: Stop (status is a terminal answer)
    -> bounded by max_rounds; one trace file for the whole loop

See docs/Week5_Agent_Task_Contract.md for the goal, state, limits and stop
conditions this loop is bound by, and docs/Week3_RAG_Architecture.md's
"Week 5 addition" section for the architecture diagram.

Week 7 wraps the same loop with guardrails that run outside the model
(src/guardrails.py): input checks, prompt-injection and prohibited-action
screening, and output checks against the tool results. Every trace now
also records the prompt, the retrieved chunks, latency and the guardrail
decision. See docs/Week7_Guardrails.md.

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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guardrails import (  # noqa: E402
    VALID_STATUSES,
    groundedness,
    screen_output,
    screen_request,
)
from llm_client import generate  # noqa: E402
from rag.retrieve import retrieve  # noqa: E402
from tools.dispatch import dispatch  # noqa: E402
from tools.registry import ALLOW_LIST  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "evidence" / "traces" / "tools"

# Week 5 Agent Task Contract's iteration limit: enough for the genuine
# two-tool chain (check_course_load -> create_defect_report -> final answer,
# 3 model turns) plus one spare round for a correction/re-plan, while still
# bounding worst-case cost. See docs/Week5_Agent_Task_Contract.md "Limits".
MAX_TOOL_ROUNDS = 3

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
  "reason": "One-line plan: why this tool, now, before anything else."
}}

If you can finish, return:

{{
  "status": "ok",
  "tool": "",
  "arguments": {{}},
  "answer": "Plain-language answer.",
  "reason": "One-line plan: why you are stopping here instead of calling another tool."
}}

Always put your one-line plan in "reason", even for "tool_call" and "ok" —
this is what makes your Plan/Decide step inspectable in the trace, not only
your final answer. A request that genuinely needs two tools in sequence
(e.g. check a rule, then draft a defect only if it was violated) should
re-plan after observing each tool result rather than calling both blindly.

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


@dataclass
class SessionState:
    """Week 6: explicit model of one handle_request() call's workflow state.

    Before Week 6 this was four loose local variables (steps, tool_results,
    model_calls, final) threaded through the loop body by hand. Naming and
    typing them is what "model workflow/session state explicitly" asks for
    — the loop's behaviour is unchanged, only its state now has a real,
    inspectable shape instead of implicit bookkeeping. See
    docs/Week6_State_Model.md for the full write-up.

    Scope and lifetime: one handle_request() call. Created at the top of
    the loop, mutated once per round, serialised into a trace file, then
    discarded — nothing here survives past the function return. That is
    the deliberate contrast with src/memory/case_history.py, the new Week 6
    persistent store that *does* survive across separate requests. A
    SessionState is the agent's short-term working memory for one task;
    case_history is its long-term memory of past outcomes.
    """

    request: str
    tag: str = ""
    steps: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    model_calls: list[dict] = field(default_factory=list)
    status: str = "in_progress"
    final: dict | None = None
    last_validation: dict | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str | None = None
    prompts: list[dict] = field(default_factory=list)
    retrieval: list[dict] = field(default_factory=list)
    guardrails: dict = field(default_factory=dict)

    def record_model_turn(self, round_i: int, model_record: dict, validation: dict) -> None:
        self.last_validation = validation
        self.model_calls.append(model_record)
        self.steps.append({
            "round": round_i,
            "kind": "model",
            "parsed": validation["parsed"],
            "schema_errors": list(validation["schema_errors"]),
        })

    def record_dispatch(self, round_i: int, tool: str | None, arguments: dict | None, result: dict) -> None:
        record = {"tool": tool, "arguments": arguments, "result": result}
        self.tool_results.append(record)
        self.steps.append({"round": round_i, "kind": "dispatch", **record})

    def stop(self, final: dict) -> None:
        """Reach a terminal status. Idempotent-safe: only the first call sets ended_at."""
        self.final = final
        self.status = final.get("status", "partial")
        if self.ended_at is None:
            self.ended_at = datetime.now(timezone.utc).isoformat()

    def to_trace_dict(self) -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": self.request,
            "tag": self.tag,
            "state": {
                "status": self.status,
                "started_at": self.started_at,
                "ended_at": self.ended_at,
                "rounds_used": len(self.tool_results),
            },
            "steps": self.steps,
            "tool_results": self.tool_results,
            "model_calls": self.model_calls,
            "validation": {k: v for k, v in (self.last_validation or {}).items() if k != "parsed"},
            "prompts": self.prompts,
            "retrieval": self.retrieval,
            "guardrails": self.guardrails,
            "metrics": self.metrics(),
            "parsed_output": self.final,
        }

    def metrics(self) -> dict:
        latency = sum(int(call.get("latency_ms") or 0) for call in self.model_calls)
        schema = (self.last_validation or {}).get("schema_errors") or []
        findings = self.guardrails.get("output_findings") or []
        if not self.model_calls:
            instruction_following: bool | str = "not_applicable"
        else:
            instruction_following = not schema and not findings
        return {
            "latency_ms": latency,
            "model_turns": len(self.model_calls),
            "tool_calls": len(self.tool_results),
            "tools_selected": [item.get("tool") for item in self.tool_results],
            "instruction_following": instruction_following,
            "safety_violations": list(self.guardrails.get("safety_violations") or []),
            "grounded": self.guardrails.get("grounded", "not_applicable"),
            "task_completion": self.final is not None and self.status in VALID_STATUSES - {"tool_call"},
        }


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


def _retrieval_records(request: str) -> list[dict]:
    """Top-k chunks for the trace and the prompt. Retrieval errors are recorded, not raised."""
    try:
        hits = retrieve(request, k=4)
    except Exception as exc:  # retrieval must not take the agent down
        return [{"error": str(exc)}]
    records = []
    for hit in hits:
        chunk = hit.chunk
        records.append({
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "title": chunk.title,
            "provenance": chunk.provenance,
            "status": chunk.status,
            "score": round(hit.score, 3),
            "text": chunk.text,
        })
    return records


def _user_prompt(request: str, prior_steps: list[dict], retrieval: list[dict]) -> str:
    body = f"## Request\n{request}\n"
    usable = [row for row in retrieval if "error" not in row]
    if usable:
        body += "\n## Retrieved context\n"
        body += (
            "Supporting chunks only. A course-load allow or deny still requires "
            "check_course_load. A chunk with status draft-unapproved is not an approved rule.\n"
        )
        for row in usable:
            body += (
                f"\n[{row['chunk_id']}] doc_id={row['doc_id']} status={row['status']} "
                f"score={row['score']}\n{row['text']}\n"
            )
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
    memory_store: Path | None = None,
    max_rounds: int = MAX_TOOL_ROUNDS,
    traces_dir: Path | None = None,
) -> dict:
    """Run the bounded agent loop. scripted_turns replace generate() for offline eval.

    One Plan/Decide model turn per round; a tool_call turn pairs with an
    Act+Observe dispatch, then re-plans next round. max_rounds bounds how
    many *tool-call* turns are allowed (Week 5 Agent Task Contract's
    iteration limit) — it does not bound the one extra turn always reserved
    for a final answer. The loop is guaranteed to reach a terminal status:
    either the model stops itself, or round max_rounds forces a safe
    "partial" stop that still reports every tool result gathered so far,
    rather than ever returning no answer at all.
    """
    state = SessionState(request=request, tag=tag)
    state.retrieval = _retrieval_records(request)
    screened = screen_request(request)
    state.guardrails = {
        "input_reasons": screened["input_reasons"],
        "injection": screened["injection"],
        "prohibited": screened["prohibited"],
        "output_findings": [],
        "safety_violations": list(screened["safety_violations"]),
        "blocked_before_model": screened["blocked"],
        "grounded": "not_applicable",
    }
    if screened["blocked"]:
        state.stop({
            "status": screened["status"],
            "tool": "",
            "arguments": {},
            "answer": screened["answer"],
            "reason": "input guardrail: " + ", ".join(screened["safety_violations"]),
        })
        return _write_trace(state, traces_dir)

    for round_i in range(max_rounds + 1):
        user = _user_prompt(request, state.tool_results, state.retrieval)
        state.prompts.append({"round": round_i, "system": SYSTEM, "user": user})
        if scripted_turns is not None:
            if round_i >= len(scripted_turns):
                validation = {
                    "json_parsed_first_try": False,
                    "json_parsed_after_repair": False,
                    "schema_errors": ["no further scripted turn"],
                    "parsed": None,
                }
                raw = ""
                model_record = {"scripted": True, "error": "no further scripted turn", "text": ""}
            else:
                raw = json.dumps(scripted_turns[round_i])
                validation = parse_and_validate(raw)
                model_record = {
                    "scripted": True,
                    "text": raw,
                    "error": None,
                    "latency_ms": 0,
                }
        else:
            resp = generate(user=user, system=SYSTEM)
            raw = resp.text
            validation = parse_and_validate(raw)
            model_record = resp.to_dict()

        state.record_model_turn(round_i, model_record, validation)
        parsed = validation["parsed"]

        if parsed is None:
            break  # state.final stays None; the post-loop fallback below stops safely

        if parsed.get("status") != "tool_call":
            findings = screen_output(parsed, state.tool_results, validation["schema_errors"], request)
            state.guardrails["output_findings"] = findings
            if findings:
                state.guardrails["safety_violations"] = list(state.guardrails["safety_violations"]) + findings
                state.guardrails["blocked_model_output"] = parsed
                state.stop({
                    "status": "refused",
                    "tool": "",
                    "arguments": {},
                    "answer": "Stopped by the output guardrail: " + ", ".join(findings) + ".",
                    "reason": "model output failed validation and was not accepted as the outcome",
                })
            else:
                state.stop(parsed)  # Stop: the model reached a terminal status itself
            break

        if round_i == max_rounds:
            # Iteration limit reached with the model still asking for a tool.
            # Stop safely now rather than spending the last round on a tool
            # call that could only ever be followed by an unbounded (max_rounds+1)th
            # model turn. Every tool result already gathered is still reported.
            state.stop({
                "status": "partial",
                "tool": "",
                "arguments": {},
                "answer": (
                    "Stopped: reached the maximum of "
                    f"{max_rounds} tool call(s) for this request before a final "
                    "answer was reached."
                ),
                "reason": f"max_rounds ({max_rounds}) exhausted; see tool_results for what was gathered",
            })
            break

        # Act: allow-list + schema live in dispatch, even if parse flagged the name.
        result = dispatch(
            str(parsed.get("tool") or ""),
            parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {},
            inject=inject if round_i == 0 else None,
            defects_dir=defects_dir,
            memory_store=memory_store,
        )
        # Observe: this result becomes part of next round's Sense input via
        # state.tool_results -> _user_prompt(). Re-plan happens on the next
        # loop turn.
        state.record_dispatch(round_i, parsed.get("tool"), parsed.get("arguments"), result)

    if state.final is None:
        # The loop ended without any terminal status (e.g. an unparseable
        # response broke the loop early). Never return a trace with no
        # answer at all — that would be an unbounded, unsafe failure mode
        # for a system whose whole point is stopping safely.
        state.stop({
            "status": "partial",
            "tool": "",
            "arguments": {},
            "answer": "Stopped: the model did not produce a usable response.",
            "reason": "no parseable terminal status before the loop ended",
        })

    state.guardrails["grounded"] = groundedness(
        state.guardrails.get("output_findings") or [],
        state.tool_results,
    )
    return _write_trace(state, traces_dir)


def _write_trace(state: SessionState, traces_dir: Path | None) -> dict:
    trace = state.to_trace_dict()
    folder = traces_dir or TRACES
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", state.request.lower())[:40].strip("-") or "empty"
    path = folder / f"{stamp}_{slug}{('_' + state.tag) if state.tag else ''}.json"
    path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    try:
        trace["_trace_path"] = str(path.relative_to(ROOT))
    except ValueError:
        trace["_trace_path"] = str(path)
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
