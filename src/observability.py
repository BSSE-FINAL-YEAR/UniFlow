"""
UniFlow QA Agent — Week 7 observability helpers.

Every rag_baseline / tool_baseline run already writes a full trace file under
evidence/traces/. This module adds what a pile of per-run trace files cannot
give on its own:

1. A run_id and a prompt fingerprint in every trace, so any result can be tied
   to the exact prompt text that produced it — even when a spec file in
   prompts/ has drifted from the running code.
2. One append-only summary line per run in evidence/logs/runs.jsonl, so
   outcomes, latency, tokens and errors across many runs can be inspected
   without opening each trace file (see src/log_summary.py).

Logging must never break the agent, so log_run() reports I/O errors instead
of raising. Records are written into the repository: never pass secrets here.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_LOG = ROOT / "evidence" / "logs" / "runs.jsonl"


def new_run_id(pipeline: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{pipeline}-{stamp}-{uuid.uuid4().hex[:6]}"


def prompt_fingerprint(*parts: str) -> str:
    """Short, stable hash of the prompt text actually sent to the model."""
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()[:12]


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def log_run(record: dict) -> None:
    try:
        RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        with RUN_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"warning: could not write run log {RUN_LOG}: {exc}", file=sys.stderr)
