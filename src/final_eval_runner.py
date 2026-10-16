"""
UniFlow QA Agent — Week 7 final evaluation runner.

Runs eval/final_eval_cases.json. Every case is deterministic: scripted model
turns, or a request the guardrail refuses before any model call. Dispatch,
allow-list, schemas and guardrails are the real code.

    python src/final_eval_runner.py
    python src/final_eval_runner.py --case W7-13

The verdict column is the mechanical discriminator for that case (did the
named guardrail or tool do the named thing). It is not a judgement of live
model prose. No API key is required.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tool_baseline import handle_request  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
TRACES = ROOT / "evidence" / "traces" / "week7"
DEFECTS = EVAL / "_final_eval_defects"


def _request_text(case: dict) -> str:
    text = case["request"]
    pad_to = case.get("pad_to")
    if pad_to and len(text) < pad_to:
        text = text + ("x" * (pad_to - len(text)))
    return text


def _bag(trace: dict) -> list[str]:
    guards = trace.get("guardrails") or {}
    bag: list[str] = []
    for key in ("safety_violations", "output_findings", "injection", "prohibited", "input_reasons"):
        bag.extend(guards.get(key) or [])
    return bag


def _check(case: dict, trace: dict) -> list[str]:
    """Return mismatch strings. Empty means every discriminator held."""
    expect = case["expect"]
    final = trace.get("parsed_output") or {}
    metrics = trace.get("metrics") or {}
    reasons: list[str] = []

    if "status" in expect and final.get("status") != expect["status"]:
        reasons.append(f"status {final.get('status')!r} != {expect['status']!r}")
    if "model_turns" in expect and metrics.get("model_turns") != expect["model_turns"]:
        reasons.append(f"model_turns {metrics.get('model_turns')} != {expect['model_turns']}")
    if "tool_count" in expect and len(trace.get("tool_results") or []) != expect["tool_count"]:
        reasons.append(f"tool_count {len(trace.get('tool_results') or [])} != {expect['tool_count']}")
    if "tools" in expect:
        got = [item.get("tool") for item in trace.get("tool_results") or []]
        if got != expect["tools"]:
            reasons.append(f"tools {got} != {expect['tools']}")
    if "tool_error" in expect:
        errors = [
            item["result"].get("tool_error")
            for item in trace.get("tool_results") or []
            if isinstance(item.get("result"), dict)
        ]
        if expect["tool_error"] not in errors:
            reasons.append(f"tool_error {expect['tool_error']!r} not in {errors}")
    if "tool_ok" in expect:
        checks = [
            item["result"]
            for item in trace.get("tool_results") or []
            if item.get("tool") == "check_course_load" and isinstance(item.get("result"), dict)
        ]
        ok = checks[0].get("ok") if checks else None
        if ok is not expect["tool_ok"]:
            reasons.append(f"tool_ok {ok!r} != {expect['tool_ok']!r}")
    if "defect_status" in expect:
        drafts = [
            item["result"]
            for item in trace.get("tool_results") or []
            if item.get("tool") == "create_defect_report" and isinstance(item.get("result"), dict)
        ]
        status = drafts[-1].get("status") if drafts else None
        if status != expect["defect_status"]:
            reasons.append(f"defect_status {status!r} != {expect['defect_status']!r}")
    if "grounded" in expect and metrics.get("grounded") != expect["grounded"]:
        reasons.append(f"grounded {metrics.get('grounded')!r} != {expect['grounded']!r}")
    if expect.get("safety_empty") and _bag(trace):
        reasons.append(f"expected no safety signals, got {_bag(trace)}")
    for needle in expect.get("safety_contains") or []:
        if needle not in _bag(trace):
            reasons.append(f"missing signal {needle}")
    if not metrics.get("task_completion"):
        reasons.append("task_completion is not true")
    if metrics.get("model_turns"):
        prompts = trace.get("prompts") or []
        if not prompts or "system" not in prompts[0] or "user" not in prompts[0]:
            reasons.append("model ran but the prompt was not in the trace")
    if "retrieval" not in trace:
        reasons.append("trace has no retrieval field")
    return reasons


def run_case(case: dict) -> tuple[dict, list[str]]:
    defects_dir = DEFECTS / case["id"]
    if defects_dir.exists():
        shutil.rmtree(defects_dir)
    defects_dir.mkdir(parents=True)
    trace = handle_request(
        _request_text(case),
        tag=case["id"],
        scripted_turns=case.get("scripted_turns", []),
        inject=case.get("inject"),
        defects_dir=defects_dir,
        memory_store=defects_dir / "memory.json",
        max_rounds=case.get("max_rounds", 3),
        traces_dir=TRACES,
    )
    return trace, _check(case, trace)


def _summary(trace: dict) -> str:
    final = trace.get("parsed_output") or {}
    metrics = trace.get("metrics") or {}
    signals = (trace.get("guardrails") or {}).get("safety_violations") or []
    return (
        f"status={final.get('status')}; tools={metrics.get('tools_selected')}; "
        f"grounded={metrics.get('grounded')}; signals={signals}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="run a single case, e.g. W7-13")
    args = ap.parse_args()

    suite = json.loads((EVAL / "final_eval_cases.json").read_text(encoding="utf-8"))
    cases = suite["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            raise SystemExit(f"no such case {args.case!r}")

    if DEFECTS.exists():
        shutil.rmtree(DEFECTS)
    DEFECTS.mkdir(parents=True)

    rows = []
    failed = 0
    print(f"\nRunning {len(cases)} final-eval case(s)\n" + "-" * 78)
    for case in cases:
        trace, mismatches = run_case(case)
        metrics = trace.get("metrics") or {}
        verdict = "PASS" if not mismatches else "FAIL"
        if mismatches:
            failed += 1
        rows.append({
            "case_id": case["id"],
            "category": case["category"],
            "status": (trace.get("parsed_output") or {}).get("status"),
            "tools": ",".join(metrics.get("tools_selected") or []),
            "task_completion": metrics.get("task_completion"),
            "groundedness": metrics.get("grounded"),
            "instruction_following": metrics.get("instruction_following"),
            "latency_ms": metrics.get("latency_ms"),
            "safety_signals": ",".join((trace.get("guardrails") or {}).get("safety_violations") or []),
            "actual_summary": _summary(trace),
            "verdict": verdict,
            "notes": "; ".join(mismatches),
            "trace": trace.get("_trace_path", ""),
        })
        print(f"{case['id']}  {verdict:<4}  {case['category']:<22} {_summary(trace)}")

    csv_path = EVAL / "final_results_v1.0.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("-" * 78)
    print(f"Wrote {csv_path.relative_to(ROOT)}  ({len(rows) - failed} pass, {failed} fail)")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
