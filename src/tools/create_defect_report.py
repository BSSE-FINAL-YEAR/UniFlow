"""Tool 2 — create_defect_report.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

Low-risk simulated side effect: write a pending_review JSON file.
There is no input field and no code path that can write any other status.
Approving a defect is a separate human step (scripts/review_defect.py).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DEFECTS_DIR = ROOT / "evidence" / "defects"

STORY_RE = re.compile(r"^US-\d{2}$")
RULE_RE = re.compile(r"^R-\d{2}(-[A-Z-]+)?$")
SEVERITIES = {"low", "medium", "high"}
REQUIRED = ("story_id", "rule_id", "title", "description", "severity")


class DefectWriteError(OSError):
    """Disk/write failure — dispatch maps this to tool_error: unavailable."""


def validate_arguments(arguments: dict) -> str | None:
    """Return a tagged reason, or None if the call may proceed.

    A `status` field is unauthorized (not invalid): the catalogue requires
    that attempted approval is visible in the error, not silently dropped.
    """
    if "status" in arguments:
        return f"unauthorized:status={arguments.get('status')!r}"

    missing = [name for name in REQUIRED if name not in arguments]
    if missing:
        return f"missing:{','.join(missing)}"

    story_id = arguments["story_id"]
    rule_id = arguments["rule_id"]
    title = arguments["title"]
    description = arguments["description"]
    severity = arguments["severity"]

    if not isinstance(story_id, str) or not STORY_RE.match(story_id):
        return "invalid:story_id must match US-NN"
    if not isinstance(rule_id, str) or not RULE_RE.match(rule_id):
        return "invalid:rule_id must match R-NN"
    if not isinstance(title, str) or not title or len(title) > 120:
        return "invalid:title must be a non-empty string of at most 120 characters"
    if not isinstance(description, str) or not description:
        return "invalid:description must be a non-empty string"
    if severity not in SEVERITIES:
        return "invalid:severity must be one of low|medium|high"
    return None


def _next_defect_id(defects_dir: Path, now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%S")
    candidate = f"DEF-{stamp}"
    if not (defects_dir / f"{candidate}.json").exists():
        return candidate
    # Same-second collision at this volume is rare; suffix rather than overwrite.
    n = 2
    while (defects_dir / f"DEF-{stamp}-{n}.json").exists():
        n += 1
    return f"DEF-{stamp}-{n}"


def run(
    story_id: str,
    rule_id: str,
    title: str,
    description: str,
    severity: str,
    *,
    defects_dir: Path | None = None,
    writer=None,
    now: datetime | None = None,
) -> dict:
    """Write one pending_review defect file. Never writes approved/rejected."""
    defects_dir = Path(defects_dir) if defects_dir is not None else DEFAULT_DEFECTS_DIR
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    try:
        defects_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DefectWriteError(str(exc)) from exc

    defect_id = _next_defect_id(defects_dir, now)
    rel_path = f"evidence/defects/{defect_id}.json"
    created_at = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record = {
        "defect_id": defect_id,
        "status": "pending_review",
        "story_id": story_id,
        "rule_id": rule_id,
        "title": title,
        "description": description,
        "severity": severity,
        "created_at": created_at,
        "path": rel_path,
    }

    dest = defects_dir / f"{defect_id}.json"
    payload = json.dumps(record, indent=2)
    try:
        if writer is not None:
            writer(dest, payload)
        else:
            dest.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise DefectWriteError(str(exc)) from exc

    return {
        "defect_id": defect_id,
        "status": "pending_review",
        "path": rel_path,
        "created_at": created_at,
    }


def output_is_valid(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    required = {"defect_id", "status", "path", "created_at"}
    if not required.issubset(obj):
        return False
    if obj["status"] != "pending_review":
        return False
    if not isinstance(obj["defect_id"], str) or not obj["defect_id"].startswith("DEF-"):
        return False
    if not isinstance(obj["path"], str) or "evidence/defects/" not in obj["path"].replace("\\", "/"):
        return False
    if not isinstance(obj["created_at"], str) or not obj["created_at"]:
        return False
    return True
