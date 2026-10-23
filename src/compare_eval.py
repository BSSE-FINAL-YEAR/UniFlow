"""
UniFlow QA Agent — Week 7 before/after comparison of two final-eval runs.

The re-test evidence for the Failure Catalogue: every case side by side,
so fixes and regressions are both visible.

    python src/compare_eval.py                     # v1.0 vs v1.1
    python src/compare_eval.py --before v1.0 --after v1.2
    python src/compare_eval.py --markdown          # table to paste into a doc

Uses each run's human verdict where one is filled, otherwise the automated
task_completion result (shown as auto:PASS / auto:FAIL).
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"
RANK = {"FAIL": 0, "auto:FAIL": 0, "PARTIAL": 1, "PASS": 2, "auto:PASS": 2}


def load(label: str) -> dict[str, dict]:
    path = EVAL / f"final_results_{label}.csv"
    if not path.exists():
        raise SystemExit(f"{path} not found")
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["case_id"]: r for r in csv.DictReader(fh)}


def outcome(row: dict | None) -> str:
    if row is None:
        return "not run"
    if row["status"] == "MODEL ERROR":
        return "MODEL ERROR"
    if row.get("verdict", "").strip():
        return row["verdict"].strip().upper()
    return f"auto:{row['task_completion']}"


def change(before: str, after: str) -> str:
    if before not in RANK or after not in RANK:
        return "?"
    delta = RANK[after] - RANK[before]
    return "fixed" if delta > 0 else "REGRESSION" if delta < 0 else ""


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare two final-eval runs")
    ap.add_argument("--before", default="v1.0")
    ap.add_argument("--after", default="v1.1")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    before, after = load(args.before), load(args.after)
    ids = sorted(set(before) | set(after))
    rows = []
    for cid in ids:
        b, a = before.get(cid), after.get(cid)
        ob, oa = outcome(b), outcome(a)
        rows.append((cid, (a or b)["category"], (b or {}).get("status", ""), (a or {}).get("status", ""),
                     ob, oa, change(ob, oa)))

    sys.stdout.reconfigure(encoding="utf-8")
    if args.markdown:
        print(f"| Case | Category | Status {args.before} | Status {args.after} | {args.before} | {args.after} | Change |")
        print("|---|---|---|---|---|---|---|")
        for r in rows:
            print("| " + " | ".join(r) + " |")
    else:
        print(f"{'case':<6} {'category':<22} {'status ' + args.before:<22} {'status ' + args.after:<22} "
              f"{args.before:<12} {args.after:<12} change")
        for r in rows:
            print(f"{r[0]:<6} {r[1]:<22} {r[2]:<22} {r[3]:<22} {r[4]:<12} {r[5]:<12} {r[6]}")

    for label, col in ((args.before, 4), (args.after, 5)):
        counts = Counter(r[col].replace("auto:", "") for r in rows)
        print(f"\n{label}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), end="")
    changes = Counter(r[6] for r in rows if r[6])
    print(f"\nfixed: {changes['fixed']}  regressions: {changes['REGRESSION']}")
    if any("auto:" in r[5] for r in rows):
        print(f"(some {args.after} outcomes are automated — fill the verdict column for the final comparison)")


if __name__ == "__main__":
    main()
