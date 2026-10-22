"""Shared test isolation: tests must never write into real evidence.

Without this, every pytest run appended scripted test runs to
evidence/logs/runs.jsonl and left trace files in evidence/traces/, mixing
test exhaust with genuine run evidence.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import observability  # noqa: E402
import rag_baseline  # noqa: E402
import tool_baseline  # noqa: E402

# Trace paths are reported relative to the repo root, so the redirect target
# must live inside it. Gitignored.
PYTEST_TRACES = ROOT / "evidence" / "traces" / "_pytest"


@pytest.fixture(autouse=True)
def _isolate_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(observability, "RUN_LOG", tmp_path / "_obs" / "runs.jsonl")
    monkeypatch.setattr(tool_baseline, "TRACES", PYTEST_TRACES / "tools")
    monkeypatch.setattr(rag_baseline, "TRACES", PYTEST_TRACES / "rag")
