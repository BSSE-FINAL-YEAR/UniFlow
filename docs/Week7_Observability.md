# UniFlow — Week 7 Observability and Tracing

Week 7 deliverable: *"Observability/tracing evidence."* The brief asks for
logs/traces capturing "useful model, prompt, retrieval, tool, latency/error
and outcome evidence."

## Two layers

| Layer | Where | One per | Use it to answer |
|---|---|---|---|
| **Trace** | `evidence/traces/rag/*.json`, `evidence/traces/tools/*.json` | Run | "What exactly happened in this one run?" — full prompt, every model turn, every tool call and result |
| **Run log** | `evidence/logs/runs.jsonl` | Run (one line) | "What is happening across runs?" — outcomes, errors, latency, tokens over many runs, without opening each trace |

Traces have existed since Week 2. Week 7 adds an `observability` block to
every trace, the run log, and `src/log_summary.py` to read it. The code is in
`src/observability.py`, wired into `src/rag_baseline.py` and
`src/tool_baseline.py`.

## What every run now records

The brief's evidence categories, and the field that captures each:

| Evidence | Field(s) in the trace's `observability` block / run log line |
|---|---|
| **Model** | `provider`, `model`, `model_turns` (agent), `model_error` / `model_errors` |
| **Prompt** | `prompt_id` (`rag_qa` or `tool_caller`) and `prompt_sha` — a 12-character fingerprint of the exact prompt text sent (see below). Full prompt text stays in the trace's `input` / `model_calls` |
| **Retrieval** (RAG) | `retrieved_doc_ids`, `retrieval_latency_ms`, `cited_sources` |
| **Tool** (agent) | `tools_called`, `tool_errors` (tool + error kind), `dispatch_latency_ms`; each dispatch step also records its own `latency_ms` |
| **Latency** | `model_latency_ms`, `total_latency_ms` (wall clock for the whole run) |
| **Errors** | `model_error(s)`, `schema_errors` (output-contract violations), `tool_errors` |
| **Outcome** | `outcome_status`; `trace` (path to the full trace from the log line) |
| **Correlation** | `run_id` (e.g. `agent-20261016T101500-a1b2c3`), `tag` (e.g. the eval case ID `FE-04`), `timestamp` |
| **Cost** | `prompt_tokens`, `completion_tokens` |

One deliberate detail: dispatch latency is recorded on the step, **not** on
the `tool_results` entry, because `tool_results` is fed back into the model's
next prompt. Putting timing there would change what the model sees, and
observability must never change behaviour
(`tests/test_observability.py::test_dispatch_latency_is_not_fed_back_into_the_prompt`).

## Why a prompt fingerprint, not just a version label

While building this, we found that `prompts/tool_caller_v1.0.md` says *"This is
the specification; `src/tool_baseline.py` is the running copy. They must stay
identical"* — but the spec file was last changed in Week 4, and Week 5 changed
the running prompt (the one-line plan in `reason`, the re-plan instruction).
A hand-maintained version label would have carried that drift silently into
every trace. `prompt_sha` is computed from the prompt text actually sent, so
any change to the running prompt produces a new fingerprint automatically,
whether or not anyone updates a file. The spec/code drift itself is a genuine
finding, recorded for the Failure Catalogue.

## Inspecting it

```
python src/log_summary.py                     # all runs: outcomes, errors, latency p50/p95/max, tokens, prompt versions
python src/log_summary.py --tag-prefix FE-    # only the final-evaluation runs
python src/log_summary.py --last 10           # plus the 10 most recent runs, one line each
```

From any log line, `trace` points to the full trace file for that run.

## What is not logged

- No API keys, `.env` contents or credentials. `llm_client.LLMResponse` carries
  none, and nothing reads `.env` into a record.
- Inputs are truncated to 200 characters in the run log. The full text is in
  the trace, and all UniFlow data is synthetic (Week 1 scope).

## Logging can never break a run

`log_run()` reports a write failure on stderr and returns. It never raises,
so a full disk or an unwritable log path cannot stop the agent
(`tests/test_observability.py::test_logging_failure_never_breaks_a_run`).

## Test runs stay out of the evidence

`tests/conftest.py` redirects the run log to a temporary file and traces to
`evidence/traces/_pytest/` (gitignored) for every test. Before this, every
`pytest` run left scripted traces in the real evidence folders, mixing test
exhaust with genuine runs. Evidence from real runs is now only evidence from
real runs.
