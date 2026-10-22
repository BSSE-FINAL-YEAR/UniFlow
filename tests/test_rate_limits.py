"""Regression tests for the Week 7 live-run failure: Gemini's free quota ran out
mid-evaluation, retries waited only 2s/4s, the runner kept spending requests on
every remaining case, and a retry overwrote FE-10's real result with an error."""
from __future__ import annotations

import csv
import sys

import pytest

import final_eval_runner as fer
import llm_client

GEMINI_429_BODY = '{"error": {"code": 429, "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "37s"}]}}'


class FakeResponse:
    def __init__(self, text="", headers=None):
        self.text = text
        self.headers = headers or {}


# -- llm_client ----------------------------------------------------------------

def test_retry_after_read_from_header():
    assert llm_client._retry_after_seconds(FakeResponse(headers={"retry-after": "12"})) == 12.0


def test_retry_after_read_from_gemini_body():
    assert llm_client._retry_after_seconds(FakeResponse(text=GEMINI_429_BODY)) == 37.0


def test_retry_after_absent():
    assert llm_client._retry_after_seconds(FakeResponse(text="{}")) is None


def test_generate_waits_as_long_as_the_provider_asks(monkeypatch):
    calls, waits = [], []

    def flaky(system, user, model, temperature):
        calls.append(1)
        if len(calls) == 1:
            raise llm_client.RateLimitError("rate limited", retry_after=37.0)
        return "{}", 1, 1

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setitem(llm_client._PROVIDERS, "gemini", (flaky, "GEMINI_MODEL", "m"))
    monkeypatch.setattr(llm_client.time, "sleep", waits.append)
    resp = llm_client.generate(user="u")
    assert resp.error is None and resp.attempts == 2
    assert waits == [37.0]


def test_provider_wait_is_capped(monkeypatch):
    waits = []

    def always_limited(system, user, model, temperature):
        raise llm_client.RateLimitError("rate limited", retry_after=3600.0)

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setitem(llm_client._PROVIDERS, "gemini", (always_limited, "GEMINI_MODEL", "m"))
    monkeypatch.setattr(llm_client.time, "sleep", waits.append)
    resp = llm_client.generate(user="u")
    assert resp.error
    assert waits and max(waits) == llm_client.MAX_RATE_LIMIT_WAIT


# -- final_eval_runner main loop -------------------------------------------------

def _outcome(error=None, **kw):
    base = {"model_error": error, "status": "ok", "answer": "4 units", "reason": "", "sources": ["KB-R04"],
            "retrieved": ["KB-R04"], "schema_errors": [], "tools_called": [], "tool_results": [],
            "new_defects": [], "duplicate_flagged": False, "latency_ms": 10, "tokens": 5,
            "model": "fake/fake", "trace": "t.json"}
    return {**base, **kw}


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.setattr(fer, "RESULTS", tmp_path / "results.csv")
    monkeypatch.setattr(fer, "SUMMARY", tmp_path / "summary.json")
    calls = []

    def run(argv, outcome_for):
        def fake_run_case(case, workroot):
            calls.append(case["id"])
            return outcome_for(case)
        monkeypatch.setattr(fer, "run_case", fake_run_case)
        monkeypatch.setattr(sys, "argv", ["final_eval_runner.py", *argv])
        fer.main()
        with open(fer.RESULTS, newline="", encoding="utf-8") as fh:
            return {r["case_id"]: r for r in csv.DictReader(fh)}

    run.calls = calls
    return run


def test_runner_stops_after_consecutive_quota_errors(runner):
    rows = runner([], lambda case: _outcome(error="rate limited (HTTP 429): quota exceeded"))
    assert runner.calls == ["FE-01", "FE-02", "FE-03"]
    assert len(rows) == 3


def test_model_error_never_overwrites_a_scored_result(runner):
    runner(["--case", "FE-01"], lambda case: _outcome())
    rows = runner(["--case", "FE-01"], lambda case: _outcome(error="HTTP 503"))
    assert rows["FE-01"]["status"] == "ok"


def test_retry_errors_also_picks_up_cases_never_run(runner):
    runner(["--case", "FE-01"], lambda case: _outcome())
    runner.calls.clear()
    runner(["--retry-errors"], lambda case: _outcome(error="HTTP 500"))
    assert "FE-01" not in runner.calls and "FE-02" in runner.calls


def test_dependent_case_skipped_when_its_memory_seed_fails(runner):
    runner(["--case", "FE-11"], lambda case: _outcome(error="HTTP 500"))
    assert runner.calls == ["FE-10"]
