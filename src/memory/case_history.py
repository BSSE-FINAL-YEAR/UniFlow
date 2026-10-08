"""
UniFlow QA Agent — Week 6 persistent memory: duplicate-defect case history.

Stores, per (rule_id, story_id), whether a defect has already been drafted
for that exact violation, so repeated detection of the same rule/story
violation does not write a near-duplicate pending_review record every time.
See docs/Week6_Memory_Design.md for what is stored, why, who can access it,
and the retention/deletion policy this module implements.

This module never decides WHETHER something is a violation — that is still
entirely check_course_load's job (R-04). Memory only prevents a duplicate
WRITE once create_defect_report is already being called for a violation
the agent itself identified; it does not change that decision.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORE = ROOT / "data" / "memory" / "case_history.json"


def _key(rule_id: str, story_id: str) -> str:
    return f"{rule_id}:{story_id}"


def _load(store: Path) -> dict:
    if not store.exists():
        return {}
    try:
        return json.loads(store.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # A corrupt memory file must never crash the agent. Treat it as
        # empty; the next successful remember_defect() call repairs it.
        return {}


def _save(store: Path, data: dict) -> None:
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_prior_defect(rule_id: str, story_id: str, store: Path | None = None) -> dict | None:
    """Return the remembered entry for this violation, or None if never seen."""
    store = store or DEFAULT_STORE
    return _load(store).get(_key(rule_id, story_id))


def remember_defect(
    rule_id: str, story_id: str, defect_id: str, path: str, store: Path | None = None
) -> dict:
    """Record that this violation now has a defect on file.

    Call once, immediately after create_defect_report successfully writes a
    NEW file. Never call this for a duplicate — dispatch() short-circuits
    before a duplicate ever reaches the write step, so remember_defect()
    only ever sees genuinely new defect_ids. Returns the stored entry.
    """
    store = store or DEFAULT_STORE
    data = _load(store)
    key = _key(rule_id, story_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing = data.get(key)
    entry = {
        "rule_id": rule_id,
        "story_id": story_id,
        "defect_id": defect_id,
        "path": path,
        "first_seen": existing["first_seen"] if existing else now,
        "last_seen": now,
        "times_seen": (existing["times_seen"] + 1) if existing else 1,
    }
    data[key] = entry
    _save(store, data)
    return entry


def forget(rule_id: str, story_id: str, store: Path | None = None) -> bool:
    """Delete the remembered entry for this violation. Returns True if one existed.

    This is the deletion half of the retention/deletion policy in
    docs/Week6_Memory_Design.md: if the defect file this entry points to is
    ever deleted from evidence/defects/, call this so memory does not
    outlive the record it refers to.
    """
    store = store or DEFAULT_STORE
    data = _load(store)
    key = _key(rule_id, story_id)
    if key not in data:
        return False
    del data[key]
    _save(store, data)
    return True
