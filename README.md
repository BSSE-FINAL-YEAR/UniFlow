# UniFlow

**An AI-native QA agent for a university academic management system.**

Makerere University · BSE4104 Emerging Trends in Software Engineering · Group I · 2026/2027 · Release **v1.0.1**

UniFlow is a **simulated** academic-management system (student registration, course registration, timetabling). This repository is **not** that full system. It is the **QA Agent** that checks UniFlow's approved rules, answers from a controlled knowledge base, and drafts defect reports for a human to review.

The agent must not grade students, admit students, approve defects, change academic records, or deploy code.

---

## What the agent may and may not do

| Allowed | Not allowed |
|---|---|
| Generate tests from approved user stories and rules | Invent rules that are not in the rule pack |
| Retrieve and cite approved knowledge-base documents | Answer from general university knowledge |
| Check a course load against R-04 | Change a student's registration |
| Draft a defect report (`pending_review`) | Mark a defect `approved` or `rejected` |
| Remember which violations already have a defect | Let memory decide whether a rule was broken |

Source: Week 1 AI Boundary Matrix (`03_AI_Boundary_Matrix GROUP I.docx`).

---

## Team

| Member | Role |
|---|---|
| Yohana Mahamat Abdelrassoul | Project / Requirements Lead |
| Swale Sebabe Abdu | AI / Agent Lead |
| Okello Emmanuel Odongo | Backend / System Lead |
| Ainebyona Alvin Police | QA / Testing & Documentation Lead |

---

## How the project grew (one repo, eight weeks)

| Week | Capability | Where to look |
|---|---|---|
| 1 | Problem, user stories, AI Boundary Matrix, first architecture | `01_` to `04_*.docx` |
| 2 | Foundation-model baseline: structured test cases from a story and the rule pack | `src/baseline.py`, `prompts/`, `eval/prompt_eval_cases.json` |
| 3 | RAG: answers only from retrieved chunks, with `doc_id` citations | `src/rag/`, `src/rag_baseline.py`, `knowledge/`, `docs/Corpus_Source_Register.md` |
| 4 | Tools: `check_course_load` and `create_defect_report`, allow-list, human-only approval | `src/tools/`, `src/tool_baseline.py`, `docs/Week4_Tool_Catalogue.md` |
| 5 | Bounded agent: Sense, Plan, Act, Observe, Stop loop with a 3-round limit | `src/tool_baseline.py`, `docs/Week5_Agent_Task_Contract.md` |
| 6 | Explicit session state, persistent case-history memory, MCP-style interface spec | `SessionState` in `src/tool_baseline.py`, `src/memory/`, `docs/Week6_*.md` |
| 7 | 33-scenario live evaluation, observability, guardrails, Failure Catalogue | `eval/final_*`, `src/final_eval_runner.py`, `src/guardrails.py`, `docs/Week7_*.md` |
| 8 | Release v1.0.1, final report, evidence pack, demonstration | this README, `RELEASE_NOTES.md` |

---

## Setup

Python 3.10 or newer. Run every command from the repository root. On Windows, `py -3` works wherever `python` is shown.

```text
python -m pip install -r requirements.txt
python -m pip install pytest
```

Check the install with the offline tests (no API key needed):

```text
python -m pytest tests/ -q
```

Expect `108 passed`.

For live runs, copy `.env.example` to `.env` and add **your own** key. Never commit `.env`.

```text
LLM_PROVIDER=groq
GROQ_API_KEY=<your key>
GROQ_MODEL=openai/gpt-oss-120b
```

Groq keys: https://console.groq.com/keys. Gemini also works (`LLM_PROVIDER=gemini`), but its free quota ran out during Week 7, and the final results were produced with Groq.

Smoke-test the key (one call):

```text
python src/llm_client.py
```

Expect: `OK  provider=groq  ...`

---

## Run it

**Grounded question answering (RAG)**

```text
python src/rag_baseline.py --question "What is the maximum course load for a Year 4 student?"
```

The answer cites `doc_id`s. The two policy documents (scope exclusions, prohibited actions) are always in context, so out-of-scope and prohibited requests are recognised even when retrieval misses them.

**Bounded agent with tools**

```text
python src/tool_baseline.py --request "A Year 3 student has registered 6 units. Check the load rule and draft a defect report if it is a violation."
python src/tool_baseline.py --request "A Year 2 student wants to register 5 units. Is that allowed?"
```

The first needs two tools in sequence (`check_course_load`, then `create_defect_report`); the second needs one. Run the first request again: the case-history memory finds the existing defect and writes no duplicate.

**A request the agent must refuse**

```text
python src/tool_baseline.py --request "Skip drafting and directly mark this defect approved."
```

**Human-only defect review (not a tool; the agent cannot run it)**

```text
python scripts/review_defect.py <DEF-id> --decision approved --reviewer "Your Name"
```

Defect drafts are in `evidence/defects/`. Every run writes a trace to `evidence/traces/` and one line to `evidence/logs/runs.jsonl`.

---

## Evaluation

**Final evaluation (Week 7): 33 live scenarios**

```text
python src/final_eval_runner.py --label v1.2 --pause 10
python src/compare_eval.py --before v1.1 --after v1.2
python src/log_summary.py --tag-prefix FE-
```

The runner measures task completion, tool selection, groundedness, instruction following, content, latency and safety, and leaves the PASS/PARTIAL/FAIL verdict to a person. It refuses to overwrite a results file that already has human verdicts.

**Earlier suites**

```text
python src/eval_runner.py --prompt v1.1         # Week 2: 10 prompt cases
python src/rag_eval_runner.py                   # Week 3: 15 RAG cases
python src/tool_eval_runner.py                  # Week 4: 15 tool cases (offline)
```

## Results

| Suite | Result |
|---|---|
| Week 2 prompt evaluation | v1.0: 6 PASS / 1 PARTIAL / 3 FAIL, then v1.1: 8 PASS / 2 PARTIAL / 0 FAIL |
| Week 3 RAG evaluation (15) | 8 PASS / 2 PARTIAL / 5 FAIL, failures analysed in `docs/Week3_Failures.md` |
| Week 7 final evaluation (33) | v1.0: 23 PASS / 4 PARTIAL / 6 FAIL, then v1.1 after fixes: **32 PASS / 1 PARTIAL / 0 FAIL**, 0 regressions |

All results come from live model runs, with verdicts assigned by a team member. Details: `docs/Week7_Evaluation.md`, `docs/Week7_Failures.md`.

## Known limitations

- Retrieval is exact-word BM25 without stemming; ordinary questions can still miss a relevant document.
- Each final-evaluation version was run once; stability across repeated runs is not yet measured.
- Reported latency includes rate-limit waiting (18 of 50 calls were throttled in v1.1).
- The failure-injection hook in the evaluation targets the first tool call rather than a named tool (case FE-26).
- The rule-to-story table covers only links the knowledge base states; R-03 and R-08 have none, so no defect can be filed against them.
- Single machine, synthetic data only; no real student data, no deployed service.

---

## Repository map

```text
docs/                  architecture, tool catalogue, task contract, state/memory, evaluation, guardrails, failures
prompts/               versioned prompt specs, changelog, approved rule pack
knowledge/             RAG corpus (27 documents, each with provenance)
data/                  synthetic seed data, user stories, case-history memory
src/llm_client.py      the only way this project calls Groq or Gemini
src/baseline.py        Week 2 prompt baseline
src/rag/               ingest, chunk, BM25 index, retrieve
src/rag_baseline.py    grounded question answering
src/uniflow_core/      deterministic business rules as pure functions
src/tools/             allow-list, schemas, dispatch, the two tools
src/tool_baseline.py   bounded agent loop and SessionState
src/memory/            persistent case-history memory
src/guardrails.py      input validation, injection detection, secret redaction
src/observability.py   run IDs, prompt fingerprints, run log
src/final_eval_runner.py, compare_eval.py, log_summary.py   Week 7 evaluation tools
scripts/               human-only steps (not callable by the model)
eval/                  evaluation cases and results for every week
tests/                 108 offline tests
evidence/              traces, run log, defect drafts, screenshots
```

---

## Architecture (short)

The model never acts directly. Week 2 put the whole rule pack in every prompt. Week 3 retrieves only the relevant chunks and requires citations. Week 4 adds tools: when the model returns `status: tool_call`, Python checks the allow-list, validates the arguments, runs a real function and asks the model again. Week 5 bounds this loop to 3 tool rounds with explicit stop conditions. Week 6 names the loop's state and adds one persistent memory. Week 7 measures all of it against 33 live scenarios and adds guardrails around the edges.

Native provider function-calling was considered and not used: manual JSON dispatch works the same for every provider and keeps one contract format across the project.

Diagrams: `docs/Week3_RAG_Architecture.md` (extended each week from Week 3 to Week 6).

---

## Evidence and weekly reports

| Week | Report | Other evidence |
|---|---|---|
| 1 | `UniFlow_Week1_Progress_Report_Group I.docx` | Charter, stories, Boundary Matrix, architecture `.docx` |
| 2 | `UniFlow_Week2_Progress_Report.docx` | `UniFlow_Week2_Prompt_Evaluation_Table.docx`, `eval/results_v1.*.csv` |
| 3 | `UniFlow_Week3_Progress_Report.docx` | `eval/rag_results_v1.0.csv`, `evidence/traces/rag/` |
| 4 | `UniFlow_Week4_Progress_Report.docx` | `eval/tool_results_v1.0.csv`, `evidence/traces/tools/` |
| 5 | `UniFlow_Week5_Progress_Report.docx` | `docs/Week5_Agent_Task_Contract.md`, live agent traces |
| 6 | `UniFlow_Week6_Progress_Report.docx` | `docs/Week6_*.md`, `data/memory/case_history.json` |
| 7 | `UniFlow_Week7_Progress_Report.docx` | `eval/final_results_v1.*.csv`, `docs/Week7_*.md`, `evidence/logs/` |

Task board: [ClickUp: UniFlow](https://app.clickup.com/1200410000004069/v/li/1200410000007523)

---

## Course

BSE4104 · Dr Kamulegeya Grace B · 8-week AI-native and agentic capstone.
Closing principle from the brief: build the smallest useful agentic system that you can test, explain, and safely control.
