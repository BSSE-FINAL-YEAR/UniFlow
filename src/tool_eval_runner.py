"""
UniFlow QA Agent — Week 4 tool evaluation runner.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

Runs eval/tool_eval_cases.json. Dispatch cases need no API key.
Orchestration_scripted cases drive tool_baseline.handle_request with
fixed model turns so the allow-list and schemas are what get tested.

    python src/tool_eval_runner.py
    python src/tool_eval_runner.py --case TQ-06

Same discipline as rag_eval_runner.py: this script records what happened.
It does not assign PASS/PARTIAL/FAIL.

Week 6 note: this suite is deliberately run against an isolated, reset-
every-run memory store (EVAL_MEMORY_STORE below), not the real
data/memory/case_history.json. TQ-13 and TQ-06/08/09/10/11 all share
rule_id="R-04"/story_id="US-08"; without isolation, TQ-13's successful
write on one run would make the identical call return duplicate_of on the
next, silently changing an already-recorded Week 4 result. Isolating (and
clearing) the store keeps this suite exactly as repeatable as it was
before Week 6 introduced persistent memory.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tool_baseline import handle_request  # noqa: E402
from tools.dispatch import dispatch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
TRACES = ROOT / "evidence" / "traces" / "tools"
EVAL_MEMORY_STORE = EVAL / "_tool_eval_memory_store.json"


def _summarise_dispatch(result: dict) -> str:
    if "tool_error" in result:
        return f"tool_error={result['tool_error']}; message=\"{result.get('message', '')[:140]}\""
    if "ok" in result:
        return f"ok={result.get('ok')}; rule={result.get('rule')}; message=\"{str(result.get('message', ''))[:120]}\""
    if "defect_id" in result:
        return f"defect_id={result.get('defect_id')}; status={result.get('status')}; path={result.get('path')}"
    return json.dumps(result)[:200]


def _write_dispatch_trace(case: dict, result: dict) -> str:
    TRACES.mkdir(parents=True, exist_ok=True)
    trace = {
        "timestamp": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "tag": case["id"],
        "mode": "dispatch",
        "tool": case.get("tool"),
        "arguments": case.get("arguments"),
        "inject": case.get("inject"),
        "result": result,
        "expected": case.get("expected"),
    }
    path = TRACES / f"{case['id']}.json"
    path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return str(path.relative_to(ROOT))


def run_case(case: dict) -> tuple[str, str]:
    mode = case.get("mode", "dispatch")
    if mode == "dispatch":
        result = dispatch(
            case["tool"],
            case.get("arguments") or {},
            inject=case.get("inject"),
            memory_store=EVAL_MEMORY_STORE,
        )
        return _summarise_dispatch(result), _write_dispatch_trace(case, result)

    if mode == "orchestration_scripted":
        trace = handle_request(
            case["request"],
            tag=case["id"],
            scripted_turns=case.get("scripted_turns") or [],
            memory_store=EVAL_MEMORY_STORE,
        )
        dispatch_bits = [_summarise_dispatch(item["result"]) for item in trace["tool_results"]]
        final = trace["parsed_output"] or {}
        actual = (
            f"final_status={final.get('status', '?')}; "
            + ("; ".join(dispatch_bits) if dispatch_bits else "no tool call")
        )
        return actual, trace["_trace_path"]

    raise SystemExit(f"unknown mode {mode!r} on {case['id']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="run a single case, e.g. TQ-06")
    args = ap.parse_args()

    # Reset the isolated memory store every run so this suite stays exactly
    # as repeatable as it was before Week 6 — see the module docstring.
    EVAL_MEMORY_STORE.unlink(missing_ok=True)

    suite = json.loads((EVAL / "tool_eval_cases.json").read_text(encoding="utf-8"))
    cases = suite["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            raise SystemExit(f"no such case {args.case!r}")

    rows = []
    print(f"\nRunning {len(cases)} tool case(s)\n" + "-" * 78)

    for case in cases:
        actual, trace_path = run_case(case)
        rows.append({
            "case_id": case["id"],
            "category": case["category"],
            "mode": case.get("mode", "dispatch"),
            "actual_summary": actual,
            "verdict": "",
            "notes": "",
            "trace": trace_path,
        })
        print(f"{case['id']}  {case['category'][:28]:<28} {actual}")

    csv_path = EVAL / "tool_results_v1.0.csv"
    fieldnames = list(rows[0])
    existing_by_id: dict[str, dict] = {}
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                existing_by_id[r["case_id"]] = r
    for r in rows:
        existing_by_id[r["case_id"]] = r
    ordered = [existing_by_id[c["id"]] for c in suite["cases"] if c["id"] in existing_by_id]

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ordered)

    print("-" * 78)
    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print("Next: fill 'verdict' (PASS/PARTIAL/FAIL) against each case's")
    print("      'expected' list in eval/tool_eval_cases.json. Do not automate this.\n")


if __name__ == "__main__":
    main()
