# UniFlow v1.0.0: final release (BSE4104 Week 8)

An AI-native QA agent for a simulated university academic-management system,
built over eight weeks by Group I. It answers from a controlled knowledge base
with citations, checks course loads with a deterministic tool, drafts defect
reports for human review, and refuses actions outside its AI Boundary Matrix.

## What is in this release

- **Foundation model:** Groq `openai/gpt-oss-120b` (Gemini supported), one client with retry and provider switch (`src/llm_client.py`).
- **Prompts:** versioned specs and changelog (`prompts/`); a test fails if the agent's spec and running prompt differ.
- **RAG:** 27-document corpus with provenance, BM25 retrieval, required citations, policy documents always in context.
- **Tools:** `check_course_load` (read-only) and `create_defect_report` (draft only, `pending_review`), behind an allow-list and argument validation.
- **Bounded agent:** Sense, Plan, Act, Observe, Stop loop, at most 3 tool rounds, explicit session state.
- **Memory:** persistent case history so a repeated violation does not create a duplicate defect.
- **Guardrails:** input validation, prompt-injection detection, secret redaction, rule-to-story authorization, human-only approval.
- **Observability:** a trace per run, a run log, prompt fingerprints, summary and comparison tools.

## Results

Final evaluation, 33 live scenarios (normal, edge, incorrect information,
adversarial, tool failure, unauthorized action):

- v1.0: 23 PASS / 4 PARTIAL / 6 FAIL
- v1.1 after fixes: **32 PASS / 1 PARTIAL / 0 FAIL**, 9 cases fixed, 0 regressions
- 108 offline tests passing

## Run it

See `README.md`: install, run `python -m pytest tests/ -q`, add a Groq key to
`.env`, then try `src/rag_baseline.py` and `src/tool_baseline.py`.

## Known limitations

See the "Known limitations" section of `README.md` and the open issues in
`docs/Week7_Failures.md`.
