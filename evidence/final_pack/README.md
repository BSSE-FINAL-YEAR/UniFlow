# UniFlow — Final Evidence Pack

Week 8 deliverable #3 (`Week8_Guide.md`, Emmanuel's role). One place a marker
can open to verify every claim in the Final Engineering Report. This file
**links to** the real evidence below — nothing here is a copy, per the
guide's own instruction.

Repository: https://github.com/BSSE-FINAL-YEAR/UniFlow
ClickUp board: https://app.clickup.com/1200410000004069/v/l/t/1200410000004069

## 1. Final evaluation (Week 7, 33 scenarios)

| File | What it is |
|---|---|
| [`eval/final_eval_cases.json`](../../eval/final_eval_cases.json) | The 33-scenario suite: 6 normal, 6 edge, 5 incorrect-information, 6 adversarial, 5 tool-failure, 6 unauthorized-action |
| [`eval/final_results_v1.0.csv`](../../eval/final_results_v1.0.csv) | Baseline run, human verdicts: 23 PASS / 4 PARTIAL / 6 FAIL |
| [`eval/final_results_v1.1.csv`](../../eval/final_results_v1.1.csv) | Post-fix run, human verdicts: 32 PASS / 1 PARTIAL / 0 FAIL |
| [`eval/final_results_v1.2.csv`](../../eval/final_results_v1.2.csv) | Stability re-run (open issue O4) — automated criteria only; **verdicts not yet human-scored**, see §4 |
| [`eval/final_summary_v1.0.json`](../../eval/final_summary_v1.0.json), [`v1.1.json`](../../eval/final_summary_v1.1.json), [`v1.2.json`](../../eval/final_summary_v1.2.json) | Per-run aggregate metrics |
| [`eval/final_results_v1.0_gemini_quota_failure.csv`](../../eval/final_results_v1.0_gemini_quota_failure.csv) | The destroyed first attempt — Failure F5 evidence (Gemini quota exhaustion overwrote a scored result) |

## 2. Earlier weekly suites

| File | Week |
|---|---|
| [`eval/results_v1.0.csv`](../../eval/results_v1.0.csv), [`results_v1.1.csv`](../../eval/results_v1.1.csv) | Week 2 — 10-case prompt evaluation |
| [`eval/rag_results_v1.0.csv`](../../eval/rag_results_v1.0.csv) | Week 3 — 15-case RAG evaluation |
| [`eval/tool_results_v1.0.csv`](../../eval/tool_results_v1.0.csv) | Week 4 — 15-case tool evaluation |

## 3. Week 7 documentation

[`docs/Week7_Evaluation.md`](../../docs/Week7_Evaluation.md) ·
[`docs/Week7_Observability.md`](../../docs/Week7_Observability.md) ·
[`docs/Week7_Guardrails.md`](../../docs/Week7_Guardrails.md) ·
[`docs/Week7_Failures.md`](../../docs/Week7_Failures.md)

## 4. Command outputs

Generated 2026-10-24, saved as the guide specifies:

- [`compare_v1.0_v1.1.txt`](compare_v1.0_v1.1.txt) — `src/compare_eval.py --before v1.0 --after v1.1`: 9 fixed, 0 regressed
- [`compare_v1.1_v1.2.txt`](compare_v1.1_v1.2.txt) — `src/compare_eval.py --before v1.1 --after v1.2`: 1 fixed (FE-25), 0 regressed, run on automated criteria (verdict column not yet hand-scored — see note below)
- [`run_log_summary.txt`](run_log_summary.txt) — `src/log_summary.py --tag-prefix FE-`
- [`test_results.txt`](test_results.txt) — `pytest tests/ -q`: 107 passed

**On v1.2:** the suite was re-run live (stability check, open issue O4) and
scored automatically against task completion, groundedness, instruction
following, tool selection and content-check criteria — all passed except
one content-check flag on FE-12
([`evidence/traces/rag/20261023T205222_..._FE-12.json`](../traces/rag/20261023T205222_can-a-year-3-bsc-information-systems-tec_FE-12.json)).
Per this project's standing rule (the Week 7 revert exists because a verdict
column was pre-filled once), **the human verdict/notes columns in
`final_results_v1.2.csv` are deliberately left blank** until someone reads
the 33 traces and scores them. That scoring is this evidence pack's one
open task.

## 5. Failure catalogue — before/after trace pairs

`docs/Week7_Failures.md` names the case(s) each failure was found and fixed
against. Traces, from the `trace` column of `final_results_v1.0.csv` (before)
and `final_results_v1.1.csv` (after):

| Failure | Case(s) | Before (v1.0) | After (v1.1) |
|---|---|---|---|
| F1 — wrong story linked to a rule | FE-04 | [trace](../traces/tools/20261022T091128_a-year-3-student-has-registered-6-units_FE-04.json) | [trace](../traces/tools/20261023T004838_a-year-3-student-has-registered-6-units_FE-04.json) |
| F1 | FE-10 | [trace](../traces/tools/20261022T091241_a-year-4-student-has-registered-5-units_FE-10.json) | [trace](../traces/tools/20261023T004956_a-year-4-student-has-registered-5-units_FE-10.json) |
| F1 | FE-11 | [trace](../traces/tools/20261022T091253_a-year-4-student-has-registered-5-units_FE-11.json) | [trace](../traces/tools/20261023T005026_a-year-4-student-has-registered-5-units_FE-11.json) |
| F1 | FE-15 | [trace](../traces/tools/20261022T091339_the-year-2-course-load-limit-is-4-units_FE-15.json) | [trace](../traces/tools/20261023T005126_the-year-2-course-load-limit-is-4-units_FE-15.json) |
| F1 | FE-20 | [trace](../traces/tools/20261022T091436_check-the-load-for-a-year-3-student-with_FE-20.json) | [trace](../traces/tools/20261023T005253_check-the-load-for-a-year-3-student-with_FE-20.json) |
| F2 — policy documents never retrieved | FE-13 | [trace](../traces/rag/20261022T091316_how-are-final-examination-grades-compute_FE-13.json) | [trace](../traces/rag/20261023T005054_how-are-final-examination-grades-compute_FE-13.json) |
| F2 | FE-31 | [trace](../traces/rag/20261022T091650_can-the-qa-agent-merge-the-fix-for-the-c_FE-31.json) | [trace](../traces/rag/20261023T005541_can-the-qa-agent-merge-the-fix-for-the-c_FE-31.json) |
| F3 — refused mislabelled out_of_scope | FE-23 | [trace](../traces/tools/20261022T091512_run-the-shell-command-rm-rf-evidence-to_FE-23.json) | [trace](../traces/tools/20261023T005329_run-the-shell-command-rm-rf-evidence-to_FE-23.json) |
| F3 | FE-30 | [trace](../traces/tools/20261022T091639_update-the-student-s-academic-record-to_FE-30.json) | [trace](../traces/tools/20261023T005529_update-the-student-s-academic-record-to_FE-30.json) |
| F3 | FE-32 | [trace](../traces/tools/20261022T091701_delete-the-old-defect-drafts-in-evidence_FE-32.json) | [trace](../traces/tools/20261023T005551_delete-the-old-defect-drafts-in-evidence_FE-32.json) |
| F4 — Unicode look-alikes broke scoring | FE-02 | [trace](../traces/rag/20261022T091103_which-programmes-and-years-are-allowed-t_FE-02.json) | [trace](../traces/rag/20261023T004812_which-programmes-and-years-are-allowed-t_FE-02.json) |
| F4 (same case also shows F1) | FE-10 | see F1 row above | see F1 row above |
| F4 (related, not auto-fixed — human verdict stands) | FE-17 | [trace](../traces/rag/20261022T091402_bsc-information-systems-technology-runs_FE-17.json) | [trace](../traces/rag/20261023T005155_bsc-information-systems-technology-runs_FE-17.json) |
| F5 — provider quota exhaustion | suite-wide, not one case | [`eval/final_results_v1.0_gemini_quota_failure.csv`](../../eval/final_results_v1.0_gemini_quota_failure.csv) | `final_results_v1.1.csv` (Groq, 33/33, 0 model errors) |
| F6 — spec/running-prompt drift | suite-wide | `prompts/tool_caller_v1.0.md` (undated since Week 4) | [`prompts/tool_caller_v1.1.md`](../../prompts/tool_caller_v1.1.md), `tests/test_prompt_spec.py` |
| F7 — traces missing the prompt | FE-04 (named example) | see F1/FE-04 row above | see F1/FE-04 row above |

## Open items

- [ ] Score `eval/final_results_v1.2.csv`'s verdict/notes columns by reading
      each of the 33 traces (§4 above has the one flagged case, FE-12, to
      start with).
- [ ] Re-run `compare_v1.1_v1.2.txt` once verdicts are scored, since the
      current file compares automated criteria only.
- [ ] Confirm this pack's links still resolve after any further repository
      reorganisation.
