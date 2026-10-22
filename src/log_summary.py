"""
UniFlow QA Agent — Week 7 run-log summary.

Reads evidence/logs/runs.jsonl (one line per rag/agent run, written by
src/observability.py) and prints aggregate evidence: outcomes, errors,
latency and tokens.

    python src/log_summary.py
    python src/log_summary.py --tag-prefix FE-      # final-eval runs only
    python src/log_summary.py --last 10             # also list the 10 latest runs
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import observability  # noqa: E402


def load(path: Path, tag_prefix: str = "") -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn line must not hide every other run
        if (record.get("tag") or "").startswith(tag_prefix):
            records.append(record)
    return records


def _percentile(values: list[int], pct: int) -> int | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return int(statistics.quantiles(values, n=100, method="inclusive")[pct - 1])


def _errored(record: dict) -> bool:
    return bool(record.get("model_error") or record.get("model_errors"))


def summarise(records: list[dict]) -> dict:
    errored = [r for r in records if _errored(r)]
    # A failed provider call returns fast; counting it would flatter latency.
    latencies = [r["total_latency_ms"] for r in records
                 if isinstance(r.get("total_latency_ms"), int) and not _errored(r)]
    tool_errors = Counter(e["kind"] for r in records for e in r.get("tool_errors") or [])
    return {
        "runs": len(records),
        "by_pipeline": dict(Counter(r.get("pipeline") for r in records)),
        "by_status": dict(Counter(r.get("outcome_status") for r in records)),
        "model_error_runs": len(errored),
        "scripted_runs": sum(1 for r in records if r.get("scripted")),
        "tool_errors_by_kind": dict(tool_errors),
        "latency_ms": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "max": max(latencies) if latencies else None,
        },
        "prompt_tokens": sum(r.get("prompt_tokens") or 0 for r in records),
        "completion_tokens": sum(r.get("completion_tokens") or 0 for r in records),
        "prompt_versions": dict(Counter(f"{r.get('prompt_id')}@{r.get('prompt_sha')}" for r in records)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarise evidence/logs/runs.jsonl")
    ap.add_argument("--log", type=Path, default=observability.RUN_LOG)
    ap.add_argument("--tag-prefix", default="", help="only runs whose tag starts with this, e.g. FE-")
    ap.add_argument("--last", type=int, default=0, help="also list the N most recent runs")
    args = ap.parse_args()

    records = load(args.log, args.tag_prefix)
    if not records:
        print(f"No runs found in {args.log}" + (f" with tag prefix {args.tag_prefix!r}" if args.tag_prefix else ""))
        return

    print(json.dumps(summarise(records), indent=2))

    if args.last:
        print(f"\nLast {args.last} run(s):")
        for r in records[-args.last:]:
            err = r.get("model_error") or (r.get("model_errors") or [None])[0]
            print(f"  {r.get('timestamp', '')[:19]}  {r.get('tag') or '-':<8} {r.get('pipeline'):<5} "
                  f"status={r.get('outcome_status')}  {r.get('total_latency_ms')}ms"
                  + (f"  ERROR: {str(err)[:60]}" if err else ""))


if __name__ == "__main__":
    main()
