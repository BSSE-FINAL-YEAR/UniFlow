"""
UniFlow QA Agent — Week 3 RAG evaluation runner.

Runs the 15 cases in eval/rag_eval_cases.json through the RAG pipeline,
saves every trace (including which chunks were retrieved) to
evidence/traces/rag/, and writes eval/rag_results_v1.0.csv.

    python src/rag_eval_runner.py
    python src/rag_eval_runner.py --case RQ-09

Same discipline as Week 2's eval_runner.py: this script records what the
pipeline did. It does not assign PASS/PARTIAL/FAIL — that judgement, against
each case's "expected" list, is mine to make and defend.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rag_baseline import answer_question  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"


def summarise(parsed: dict | None, validation: dict) -> str:
    if parsed is None:
        return f"UNPARSEABLE. {'; '.join(validation['schema_errors']) or 'no JSON found'}"
    bits = [f"status={parsed.get('status', '?')}", f"sources={parsed.get('sources', [])}"]
    if parsed.get("reason"):
        bits.append(f"reason=\"{str(parsed['reason'])[:100]}\"")
    if validation["schema_errors"]:
        bits.append(f"schema_errors={len(validation['schema_errors'])}")
    return "; ".join(bits)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="run a single case, e.g. RQ-09")
    ap.add_argument("--k", type=int, default=4)
    args = ap.parse_args()

    suite = json.loads((EVAL / "rag_eval_cases.json").read_text())
    cases = suite["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            raise SystemExit(f"no such case {args.case!r}")

    rows = []
    print(f"\nRunning {len(cases)} RAG case(s)\n" + "-" * 78)

    for case in cases:
        trace = answer_question(case["question"], k=args.k, tag=case["id"])
        m, v = trace["model"], trace["validation"]
        parsed = trace["parsed_output"]

        actual = f"MODEL ERROR: {m['error']}" if m["error"] else summarise(parsed, v)
        retrieved_ids = [r["doc_id"] for r in trace["retrieved"]]

        rows.append({
            "case_id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "actual_summary": actual,
            "retrieved_doc_ids": ";".join(retrieved_ids),
            "latency_ms": m["latency_ms"],
            "verdict": "",
            "notes": "",
            "trace": trace["_trace_path"],
        })
        print(f"{case['id']}  {case['category'][:22]:<24} {actual[:90]}")

    csv_path = EVAL / "rag_results_v1.0.csv"
    fieldnames = list(rows[0])
    existing_by_id: dict[str, dict] = {}
    if csv_path.exists():
        with csv_path.open(newline="") as fh:
            for r in csv.DictReader(fh):
                existing_by_id[r["case_id"]] = r
    for r in rows:
        existing_by_id[r["case_id"]] = r
    ordered = [existing_by_id[c["id"]] for c in suite["cases"] if c["id"] in existing_by_id]

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ordered)

    print("-" * 78)
    print(f"Wrote {csv_path.relative_to(ROOT)}")
    print("Next: open the CSV and fill 'verdict' (PASS/PARTIAL/FAIL) against each")
    print("      case's 'expected' list in eval/rag_eval_cases.json. Do not automate this.\n")


if __name__ == "__main__":
    main()
