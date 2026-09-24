# UniFlow

**An AI-native QA agent for a university academic management system.**

Makerere University · BSE4104 Emerging Trends in Software Engineering · Group I · 2026/2027

UniFlow is a **simulated** academic-management system (registration, timetabling, academic records). This repository is **not** that full system. It is the **QA Agent** that checks UniFlow’s approved rules, answers from a controlled knowledge base, and drafts defect reports for a human to review.

The agent must not grade students, admit students, approve defects, change academic records, or deploy code.

---

## What the agent may and may not do

| Allowed | Not allowed |
|---|---|
| Generate tests from approved user stories and rules | Invent rules that are not in the rule pack |
| Retrieve and cite approved knowledge-base documents | Answer from general university knowledge |
| Check a course load against R-04 | Change a student’s registration |
| Draft a defect report (`pending_review`) | Mark a defect `approved` or `rejected` |
| Refuse prohibited or out-of-scope requests | Access `.env`, secrets, or production systems |

Those boundaries come from Week 1’s AI Boundary Matrix and `prompts/context/uniflow_rules.md` (R-01 to R-09).

---

## Team

| Member | Role |
|---|---|
| Yohana Mahamat Abdelrassoul | Project / Requirements Lead |
| Swale Sebabe Abdu | AI / Agent Lead |
| Okello Emmanuel Odongo | Backend / System Lead |
| Ainebyona Alvin Police | QA / Testing & Documentation Lead |

---

## How the project grows (one repo, eight weeks)

| Week | Capability | Where to look |
|---|---|---|
| 1 | Problem, user stories, AI Boundary Matrix, first architecture | `01_`–`04_*.docx`, `UniFlow_Week1_Progress_Report_Group I.docx` |
| 2 | Foundation-model baseline: generate structured test cases from a story + rule pack | `src/baseline.py`, `prompts/`, `eval/prompt_eval_cases.json` |
| 3 | RAG: answer only from retrieved chunks, with `doc_id` citations | `src/rag/`, `src/rag_baseline.py`, `knowledge/` |
| 4 | Tools: `check_course_load` and `create_defect_report`, allow-list, human approval | `src/tools/`, `src/tool_baseline.py`, `docs/Week4_Tool_Catalogue.md` |
| 5–8 | Bounded agent loop, memory, evaluation/guardrails, final release | Not built yet |

---

## Setup

Python 3.10+ recommended. Run every command from the repository root.

```text
python -m pip install -r requirements.txt
python -m pip install pytest
```

Copy `.env.example` to `.env` and add **your own** keys. Never commit `.env`.

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
```

- Gemini (primary): https://aistudio.google.com/apikey
- Groq (fallback): https://console.groq.com/keys

If Gemini is rate-limited, set `LLM_PROVIDER=groq`.

Smoke-test the key:

```text
python src/llm_client.py
```

Expect: `OK  provider=gemini  ...`

---

## Run the current capabilities

**Week 2 — test-case generation (needs a key)**

```text
python src/baseline.py --story US-08 --prompt v1.1
python src/eval_runner.py --prompt v1.1
```

**Week 3 — grounded question answering (needs a key)**

```text
python src/rag_baseline.py --question "What is the max course load in Year 3?"
python src/rag_eval_runner.py
```

**Week 4 — tool calling (needs a key for the live loop)**

```text
python src/tool_baseline.py --request "Is 6 units allowed for a Year 3 student?"
python src/tool_eval_runner.py
```

Year 3 maximum is **5 units** (R-04). The live demo should call `check_course_load` and answer from the tool result, not from memory.

**Human-only defect review (not a tool)**

```text
python scripts/review_defect.py DEF-20260924T160404 --decision approved --reviewer "Your Name"
```

The agent cannot run this. It can only draft `pending_review` files under `evidence/defects/`.

**Offline tests (no API key)**

```text
python -m pytest tests/ -q
```

---

## Repository map

```text
docs/                 architecture, tool catalogue, corpus register
prompts/              versioned prompt specs and the approved rule pack
knowledge/            Week 3 RAG corpus (frontmatter + body)
src/llm_client.py     only way this project talks to Gemini / Groq
src/baseline.py       Week 2 prompt baseline
src/rag/              ingest → chunk → BM25 → retrieve
src/rag_baseline.py   Week 3 grounded QA
src/uniflow_core/     deterministic rules (R-01–R-07) as pure functions
src/tools/            Week 4 allow-list, schemas, dispatch
src/tool_baseline.py  Week 4 tool-calling loop
scripts/              human-only steps (not callable by the model)
eval/                 evaluation cases and result CSVs
tests/                offline unit tests
evidence/traces/      one JSON trace per run (input, output, validation)
evidence/defects/     drafted defect reports
```

---

## Architecture (short)

Week 2 stuffed the whole rule pack into every prompt.  
Week 3 retrieves only the top-k chunks for that question and requires `sources`.  
Week 4 sits on top of that: if the model returns `status: tool_call`, Python checks an **allow-list**, validates arguments, runs a real function, and calls the model again.

Native provider function-calling (Gemini `functionDeclarations` / Groq `tools`) was **considered and not used**. Manual JSON-dispatch matches `baseline.py` and `rag_baseline.py` and does not add a third schema per provider.

Diagrams: `docs/Week3_RAG_Architecture.md`  
Tool contracts: `docs/Week4_Tool_Catalogue.md`

---

## Evidence and weekly reports

| Week | Report | Other evidence |
|---|---|---|
| 1 | `UniFlow_Week1_Progress_Report_Group I.docx` | Charter, stories, Boundary Matrix, architecture `.docx` |
| 2 | `UniFlow_Week2_Progress_Report.docx` | `UniFlow_Week2_Prompt_Evaluation_Table.docx`, `eval/results_v1.*.csv` |
| 3 | `UniFlow_Week3_Progress_Report.docx` | `eval/rag_results_v1.0.csv`, `evidence/traces/rag/` |
| 4 | `UniFlow_Week4_Progress_Report.docx` | `eval/tool_results_v1.0.csv`, `evidence/traces/tools/` |

Task board: [ClickUp — UniFlow](https://app.clickup.com/1200410000004069/v/li/1200410000007523)

---

## Course

BSE4104 · Dr Kamulegeya Grace B · 8-week AI-native & agentic capstone.  
Closing principle from the brief: build the smallest useful agentic system that you can test, explain, and safely control.
