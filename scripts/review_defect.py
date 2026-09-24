"""Human-only defect review. NOT a tool. Never imported by src/tools/.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

Usage:
    python scripts/review_defect.py DEF-20260924T180000 --decision approved --reviewer "Name"
    python scripts/review_defect.py DEF-20260924T180000 --decision rejected --reviewer "Name"

This is the Week 1 Boundary Matrix rule: the agent may draft, a human accepts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFECTS = ROOT / "evidence" / "defects"
ALLOWED = {"approved", "rejected"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Human review of a UniFlow defect draft")
    ap.add_argument("defect_id")
    ap.add_argument("--decision", required=True, choices=sorted(ALLOWED))
    ap.add_argument("--reviewer", required=True)
    args = ap.parse_args()

    path = DEFECTS / f"{args.defect_id}.json"
    if not path.exists():
        raise SystemExit(f"no such defect file: {path}")

    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "pending_review":
        raise SystemExit(
            f"refusing to overwrite status {record.get('status')!r}; "
            "only pending_review drafts can be reviewed here"
        )

    record["status"] = args.decision
    record["reviewed_by"] = args.reviewer
    record["reviewed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"{args.defect_id} -> {args.decision} by {args.reviewer}")


if __name__ == "__main__":
    sys.exit(main())
