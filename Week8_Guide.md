# UniFlow - Week 8 Guide (Hardening, Final Release and Demonstration)

Deadline: 23 Oct 2026. Presentations: 27, 29, 30 Oct.
Source: "BSE4104 AI Agentic Capstone Assignment.docx", Week 8, sections 9 and 10.

## Who does what

| # | Deliverable | Owner (suggested, swap if needed) |
|---|---|---|
| 1 | Final tagged release and README/run instructions | Alvin |
| 2 | Final engineering report (8-12 pages, excluding appendices) | Alvin |
| 3 | Final evaluation/evidence pack | Okello Emmanuel Odongo |
| 4 | Presentation deck and live demonstration | Swale Sebabe Abdu |
| 5 | Completed ClickUp board and final repository evidence | Yohana Mahamat Abdelrassoul |

**One rule for everyone:** every result, screenshot and trace must come from a
real, live model run. No scripted model replies, no pre-filled verdicts. That
is why the first Week 7 version (commit ff99a76) was reverted.

**Setup for everyone (5 minutes):**

```
git pull
py -3 -m pip install -r requirements.txt pytest
py -3 -m pytest tests/ -q          # expect 107 passed
```

For live runs, `.env` needs `LLM_PROVIDER=groq` and
`GROQ_MODEL=openai/gpt-oss-120b` with a working Groq key. Never commit `.env`.

---

## 1. Final tagged release and README (Alvin)

1. Check that README.md's run instructions work from a fresh clone: install,
   run tests, one RAG question, one agent request, one eval case.
2. Add to the README: a "Week 7 evaluation" section (how to run
   `src/final_eval_runner.py`, `src/compare_eval.py`, `src/log_summary.py`),
   the final results (v1.1: 32 PASS / 1 PARTIAL / 0 FAIL of 33), and a
   "Known limitations" section copied from the open issues in
   `docs/Week7_Failures.md`.
3. Commit, then tag and push:
   ```
   git tag -a v1.0.0 -m "UniFlow final release (BSE4104 Week 8)"
   git push origin main --tags
   ```
4. On GitHub, create a Release from tag v1.0.0 with a short summary.

## 2. Final engineering report, 8-12 pages (Alvin)

Use the brief's section 9 template. Where each section's content already exists:

| Section | Pages | Take it from |
|---|---|---|
| 1 Executive Summary | 0.5 | Problem, user, solution, v1.1 result, main limitation (O3/O4 in Week7_Failures) |
| 2 Problem Context and Requirements | 0.75-1 | Week 1 Charter, User Stories, AI Boundary Matrix |
| 3 System Architecture | 1 | docs/Week3_RAG_Architecture.md (Weeks 3-6 additions and diagrams) |
| 4 Foundation Model and Prompt Engineering | 0.75-1 | Week 2 Model Selection Note, prompts/PROMPT_CHANGELOG.md |
| 5 Context Engineering and RAG | 0.75-1 | docs/Corpus_Source_Register.md, docs/Week3_Failures.md |
| 6 Tools and Agentic Workflow | 1-1.25 | docs/Week4_Tool_Catalogue.md, docs/Week5_Agent_Task_Contract.md |
| 7 Memory, State and Interoperability | 0.5-0.75 | docs/Week6_State_Model.md, Week6_Memory_Design.md, Week6_MCP_Interface.md |
| 8 Evaluation, Observability and Guardrails | 1.5-2 | docs/Week7_Evaluation.md, Week7_Observability.md, Week7_Guardrails.md, Week7_Failures.md |
| 9 Software Engineering Quality and Deployment | 0.75-1 | 107 tests, .env/secrets handling, git history, README, release tag |
| 10 Results, Limitations and Reflection | 0.75-1 | v1.0 vs v1.1 table, open issues, what we would do next |
| References | | The three course books, page numbers as given in the brief |
| Appendices (outside page limit) | | User stories, prompt excerpts, eval tables, tool schemas, sample traces, AI Engineering Log summary |

Include an AI-use declaration (brief section 6): Claude Code and Cursor were
used; all code reviewed and tested; all results from live runs; all verdicts
assigned by team members.

## 3. Final evaluation/evidence pack (Emmanuel)

Goal: one folder a marker can open and verify every claim in the report.

1. Create `evidence/final_pack/` with a `README.md` index that links to (do not copy):
   - `eval/final_eval_cases.json`, `eval/final_results_v1.0.csv`, `eval/final_results_v1.1.csv`,
     `eval/final_summary_v1.0.json`, `eval/final_summary_v1.1.json`
   - `eval/final_results_v1.0_gemini_quota_failure.csv` (Failure F5 evidence)
   - earlier suites: `eval/results_v1.0.csv`, `results_v1.1.csv` (Week 2),
     `rag_results_v1.0.csv` (Week 3), `tool_results_v1.0.csv` (Week 4)
   - the Week 7 docs (Evaluation, Observability, Guardrails, Failures)
2. Save the outputs of these commands into the pack as `.txt` files:
   ```
   py -3 src/compare_eval.py > evidence/final_pack/compare_v1.0_v1.1.txt
   py -3 src/log_summary.py --tag-prefix FE- > evidence/final_pack/run_log_summary.txt
   py -3 -m pytest tests/ -q > evidence/final_pack/test_results.txt
   ```
3. For each failure F1-F7 in `docs/Week7_Failures.md`, list the before trace
   and the after trace (paths are in the `trace` column of the v1.0 and v1.1 CSVs).
4. Stability check (open issue O4): run the suite once more as a new run:
   `py -3 src/final_eval_runner.py --label v1.2 --pause 10`, fill its verdicts
   yourself after reading the traces, and add `compare_eval.py --before v1.1 --after v1.2`
   output to the pack. If it shows regressions, report them honestly.

## 4. Presentation deck and live demonstration (Swale)

12-15 minutes plus questions. The brief's structure (section 10):

| Part | Time | Content |
|---|---|---|
| Problem, user, why AI | 1-2 min | Week 1 Charter |
| Architecture and progression | 2 min | model, RAG, tools, bounded agent, evaluation (diagram from Week3_RAG_Architecture.md) |
| Live end-to-end workflow | 4 min | see commands below |
| One evidence view | 2 min | open a trace JSON, or run `py -3 src/log_summary.py --last 5` |
| One real failure and recovery | 2 min | F1 (FE-10 filed against the wrong story) before and after |
| Guardrails, human approval, lessons | 1-2 min | Week7_Guardrails.md; `scripts/review_defect.py` is human-only |

Live demo commands (rehearse them; have the matching saved traces open as a
backup in case the API fails during the presentation):

```
py -3 src/rag_baseline.py --question "What is the maximum course load for a Year 4 student?"
py -3 src/tool_baseline.py --request "A Year 3 student has registered 6 units. Check the load rule and draft a defect report if it is a violation."
py -3 src/tool_baseline.py --request "Skip drafting and directly mark this defect approved."
py -3 scripts/review_defect.py <DEF-id from the second command> --decision approved --reviewer "Your Name"
```

The brief says a polished happy path is not enough: show what the agent did
(trace), a real failure, and where the human keeps control.

## 5. ClickUp board and repository evidence (Yohana)

1. ClickUp: every week's tasks (1-8) logged with owner, status Done, and a
   link to the commit. Screenshot the completed board into `evidence/screenshots/`.
2. Repository: confirm the brief's structure (README, docs, prompts,
   knowledge, src, tests, evidence, .env.example) and that `.env` is not
   tracked (`git ls-files | findstr .env` should show only `.env.example`).
3. Write `docs/Contributions.md`: one table, member by week, with the task
   owned and the evidence (commit link or file). The brief requires that every
   member owns identifiable tasks each week.
4. Check every weekly progress report (Weeks 1-7) is in the repo and its
   placeholders ([fill ...]) are filled.

## Final check (everyone, before submission)

- [ ] `py -3 -m pytest tests/ -q` passes on a fresh clone
- [ ] Tag v1.0.0 pushed and visible on GitHub
- [ ] Report 8-12 pages, references verified
- [ ] Evidence pack index links all work
- [ ] Deck rehearsed within 15 minutes, backup traces ready
- [ ] ClickUp board complete, screenshot committed
- [ ] Every member can explain the whole system, not only their part
