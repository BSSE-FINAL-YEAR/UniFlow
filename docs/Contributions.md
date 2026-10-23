# UniFlow — Contributions by Member and Week

Required by `Week8_Guide.md` deliverable #5 (Yohana) and the capstone brief's
"every member must own identifiable tasks per week." Built directly from
`git log` — every row is a real commit, not a claim. ClickUp task links are
not included here because ClickUp requires an authenticated session this
log could not reach; add them alongside the commit links below once the
board is final. See `evidence/screenshots/` for the board screenshot (still
to be added — see Open items).

Repository: https://github.com/BSSE-FINAL-YEAR/UniFlow
ClickUp board: https://app.clickup.com/1200410000004069/v/l/t/1200410000004069

Git identity → team member:
`Swale.sebabeabdu` = Swale Sebabe Abdu · `Alvin170803` / `Ainebyona .P. Alvin` = Ainebyona Alvin Police
· `MahamatAbdelrassoul` = Yohana Mahamat Abdelrassoul · `Emmanuel Okello` = Okello Emmanuel Odongo

---

## Week 1 — Problem framing

| Member | Task | Evidence |
|---|---|---|
| Swale Sebabe Abdu | Repository setup, initial commits | [`bcc6138`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/bcc6138), [`e044cb8`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/e044cb8) |

Project Charter, User Stories, AI Boundary Matrix and Architecture
Description exist as the four `01_`–`04_*.docx` files in the repository
root; their individual authorship is recorded on the documents themselves,
not in a commit — **needs confirmation from the team** on who to credit here.

## Week 2 — Foundation model and prompting

| Member | Task | Evidence |
|---|---|---|
| Ainebyona Alvin Police | Week 2 work, Gemini model config | [`a49aaf3`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/a49aaf3), [`644dd64`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/644dd64) |
| Swale Sebabe Abdu | Baseline model interaction, prompt v1.0/v1.1, 10-case evaluation, harness bug fixes | [`e7ed6e8`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/e7ed6e8), [`77a0fb2`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/77a0fb2) |

## Week 3 — Context engineering and RAG

| Member | Task | Evidence |
|---|---|---|
| Ainebyona Alvin Police | Week 2 Playbook formatting/roles, Week 3 RAG build, evidence traces, RAG results, Week 3 Failures and Progress Report, knowledge-base rule additions | [`aa09003`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/aa09003), [`d9eccda`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/d9eccda), [`87cabf7`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/87cabf7), [`e6defb0`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/e6defb0), [`d22fec7`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/d22fec7), [`8500801`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/8500801) |

## Week 4 — Tools and function calling

| Member | Task | Evidence |
|---|---|---|
| Ainebyona Alvin Police | Tool Catalogue, defects evidence, Week 3 RAG test edits, more evidence traces | [`89e9e2d`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/89e9e2d), [`2aede9d`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/2aede9d), [`ee362d7`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/ee362d7), [`607fb5a`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/607fb5a), [`c269858`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/c269858) |
| Yohana Mahamat Abdelrassoul | Tool calling implementation, evaluation traces, Week 4 progress report, project README | [`ff91be9`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/ff91be9), [`d4219b1`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/d4219b1), [`66e09fe`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/66e09fe), [`f6bf635`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/f6bf635) |

## Week 5 — Agent architecture and bounded autonomy

| Member | Task | Evidence |
|---|---|---|
| Swale Sebabe Abdu | Bounded agent loop, task contract, stop-condition bug fix, three execution traces | [`5e7f2bc`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/5e7f2bc), [`a0c327e`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/a0c327e) |

## Week 6 — Memory, state and interoperability

| Member | Task | Evidence |
|---|---|---|
| Ainebyona Alvin Police | Week 6 deliverables (state model, memory design, MCP interface), progress report draft and updates | [`6c9761e`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/6c9761e), [`e90c87d`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/e90c87d), [`739d9c5`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/739d9c5) |

## Week 7 — Evaluation, observability and guardrails

| Member | Task | Evidence |
|---|---|---|
| Okello Emmanuel Odongo | First evaluation/guardrails/failure-catalogue attempt (Cursor-assisted) | [`ff99a76`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/ff99a76) — **reverted**, see next row |
| Ainebyona Alvin Police | Reverted the scripted-evaluation attempt (Claude-assisted review caught pre-filled verdicts); redid Week 7 live against a real model: evaluation set, guardrails, test prompt specs, full-suite re-run, failure catalogue and report | [`be87505`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/be87505), [`3bcfc67`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/3bcfc67), [`2c51baf`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/2c51baf), [`ef92fe4`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/ef92fe4), [`f68c18f`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/f68c18f) |

## Week 8 — Hardening, final release and demonstration

| Member | Task | Evidence |
|---|---|---|
| Ainebyona Alvin Police | Release notes, final engineering report draft | [`953fe69`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/953fe69) |
| Swale Sebabe Abdu | Final presentation deck + live-demo cue sheet; AI Engineering Log; report fixes (architecture diagram, AI-log link); v1.2 stability re-run (mechanical part, for Emmanuel to score) | [`c10d800`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/c10d800), [`78a8bcc`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/78a8bcc), [`22d3eb4`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/22d3eb4), [`cc6cabe`](https://github.com/BSSE-FINAL-YEAR/UniFlow/commit/cc6cabe) |

---

## Open items

- [ ] **Yohana**: ClickUp board screenshot into `evidence/screenshots/`, and
      confirm every week's ClickUp tasks are logged Done with commit links
      — this file only has GitHub evidence; ClickUp itself needs a signed-in
      pass by someone on the team.
- [ ] **Week 1** authorship of the four `.docx` deliverables — confirm and
      add to this table.
- [ ] **Emmanuel**: score the v1.2 stability run's verdicts
      (`eval/final_results_v1.2.csv`) and fold this file's Week 8 row in
      with that work once `evidence/final_pack/` exists.
