"""Week 7 observability: every run carries a run_id, prompt fingerprint and
latency/token/error totals, and appends one line to the run log."""
from __future__ import annotations

import json

import observability
import rag_baseline
import tool_baseline
from llm_client import LLMResponse
from tool_baseline import handle_request

TURNS = [
    {"status": "tool_call", "tool": "check_course_load",
     "arguments": {"year_of_study": 3, "units_requested": 6}, "answer": "", "reason": "check first"},
    {"status": "tool_call", "tool": "check_course_load",
     "arguments": {"year_of_study": 3}, "answer": "", "reason": "deliberately malformed"},
    {"status": "ok", "tool": "", "arguments": {}, "answer": "Not allowed.", "reason": "done"},
]


def _read_log() -> list[dict]:
    return [json.loads(line) for line in observability.RUN_LOG.read_text(encoding="utf-8").splitlines()]


def test_agent_trace_has_observability_block(tmp_path):
    trace = handle_request("Year 3, 6 units?", tag="obs", scripted_turns=TURNS,
                           defects_dir=tmp_path, memory_store=tmp_path / "m.json")
    obs = trace["observability"]
    assert obs["run_id"].startswith("agent-")
    assert obs["prompt_sha"] == tool_baseline.PROMPT_SHA and len(obs["prompt_sha"]) == 12
    assert obs["scripted"] is True
    assert obs["tools_called"] == ["check_course_load", "check_course_load"]
    assert obs["tool_errors"] == [{"tool": "check_course_load", "kind": "missing_parameter"}]
    assert obs["outcome_status"] == "ok"
    assert isinstance(obs["total_latency_ms"], int)
    dispatch_steps = [s for s in trace["steps"] if s["kind"] == "dispatch"]
    assert all(isinstance(s["latency_ms"], int) for s in dispatch_steps)


def test_dispatch_latency_is_not_fed_back_into_the_prompt(tmp_path):
    trace = handle_request("Year 3, 6 units?", scripted_turns=TURNS,
                           defects_dir=tmp_path, memory_store=tmp_path / "m.json")
    assert all("latency_ms" not in r for r in trace["tool_results"])


def test_agent_run_appends_one_log_line(tmp_path):
    handle_request("Year 3, 6 units?", tag="obs-log", scripted_turns=TURNS,
                   defects_dir=tmp_path, memory_store=tmp_path / "m.json")
    lines = _read_log()
    assert len(lines) == 1
    assert lines[0]["tag"] == "obs-log"
    assert lines[0]["pipeline"] == "agent"
    assert lines[0]["trace"].endswith(".json")


def test_rag_run_logs_retrieval_and_model_evidence(monkeypatch):
    fake = LLMResponse(
        text='{"status": "ok", "answer": "5 units.", "sources": ["KB-R04"], "reason": ""}',
        provider="fake", model="fake-1", temperature=0.2, latency_ms=12,
        prompt_tokens=100, completion_tokens=10, attempts=1,
    )
    monkeypatch.setattr(rag_baseline, "generate", lambda **_: fake)
    trace = rag_baseline.answer_question("What is the Year 3 course load limit?", tag="obs-rag")
    obs = trace["observability"]
    assert obs["run_id"].startswith("rag-")
    assert obs["prompt_sha"] == rag_baseline.PROMPT_SHA
    assert obs["model_latency_ms"] == 12 and obs["prompt_tokens"] == 100
    assert "KB-R04" in obs["retrieved_doc_ids"]
    assert obs["cited_sources"] == ["KB-R04"]
    assert _read_log()[0]["outcome_status"] == "ok"


def test_logging_failure_never_breaks_a_run(tmp_path, monkeypatch):
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setattr(observability, "RUN_LOG", blocker / "runs.jsonl")
    trace = handle_request("Year 3, 6 units?", scripted_turns=TURNS,
                           defects_dir=tmp_path, memory_store=tmp_path / "m.json")
    assert trace["parsed_output"]["status"] == "ok"


def test_prompt_fingerprint_changes_when_prompt_changes():
    assert observability.prompt_fingerprint("a", "b") != observability.prompt_fingerprint("a", "c")
    assert observability.prompt_fingerprint("a", "b") == observability.prompt_fingerprint("a", "b")
