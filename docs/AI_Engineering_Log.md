<!-- # UniFlow — AI Engineering Log

Required by the capstone brief §6 ("Keep a concise AI Engineering Log for
material AI-assisted decisions or generated artefacts") and referenced in
the Final Engineering Report's AI-use declaration (brief §9, §6).

**Scope.** This logs *material* AI-assisted decisions and generated
artefacts — not every autocomplete suggestion. A material entry is one
where the AI either (a) produced a non-trivial artefact a reviewer would
want to know was AI-drafted, or (b) changed a real engineering decision
(found a bug, reverted bad evidence, chose an architecture). Each entry
names the tool, what it was asked to do, what a human reviewed/changed, and
why it mattered — the brief's requirement that "students remain accountable
... and must be able to explain any AI-generated artefacts" is the test
every entry below is written to pass.

**Tools used on this project, by name:** Claude Code (Anthropic) and Cursor.
Both are declared per brief §6; see the per-week entries below for which
tool touched which week.

---

## Week 2 — Claude Code (Swale)

- **Harness bugs found and fixed, not just features added.** While running
  the Week 2 evaluation, Claude Code found that `baseline.py` never passed
  the real `story_id` into the prompt (the model had to guess it), that
  `REQUIRED_CASE_FIELDS` didn't actually enforce the `rule_source` field
  the output contract declared required, and that `eval_runner.py --case`
  silently overwrote the results CSV for every other case. All three were
  reviewed, fixed, and covered by new tests in the same session — see
  `prompts/PROMPT_CHANGELOG.md` and commit `e7ed6e8`.
- **Prompt v1.1 built from confirmed v1.0 failures only.** One hypothesised
  change from the original scaffold (bare-JSON enforcement) was reviewed
  against the actual trace evidence, found unnecessary (10/10 traces were
  already clean JSON — the API layer already enforced it), and deliberately
  dropped rather than kept for its own sake. Reasoning recorded in
  `prompts/qa_test_designer_v1.1.md` §0.
- **Human-reviewed:** every verdict in `eval/results_v1.0.csv` /
  `results_v1.1.csv` was scored by reading the actual model output against
  the case's expected list, not auto-assigned.

## Week 3 — RAG (Alvin)

Commits `87cabf7`, `e6defb0`, `d22fec7`, `8500801` carry no AI-tool
declaration. **Needs Alvin's input:** which parts of `src/rag/`,
`docs/Week3_RAG_Architecture.md`, and the 15-case RAG evaluation were
AI-assisted, and what was reviewed/changed before accepting them.

## Week 4 — Tools (Alvin, Yohana/MahamatAbdelrassoul)

Commits `89e9e2d`, `ee362d7`, `2aede9d`, `ff91be9`, `d4219b1`, `66e09fe`,
`f6bf635` carry no AI-tool declaration. **Needs team input:** same as
above — which artefacts (the Tool Catalogue, `src/tools/`, the 15-case
tool evaluation) were AI-assisted.

## Week 5 — Bounded agent loop (Claude Code, Swale)

- **Extended the Week 4 loop into an explicit Sense→Plan→Act→Observe→Stop
  agent**, per `docs/Week5_Agent_Task_Contract.md` (written before the code
  changes, not after, so the contract wasn't rationalising whatever the
  code happened to do).
- **Found and fixed a real latent bug**, not a hypothetical one: a
  `tool_call` arriving on the last allowed round previously fell through to
  an unenforced `continue` in live mode, so `handle_request()` could return
  `parsed_output: None` if the model never volunteered a terminal status.
  Caught by reasoning through what "stop safely" must guarantee, not by an
  existing test — no prior test or eval case had ever driven the loop that
  far. Fixed, and two new regression tests added
  (`tests/test_tools.py::test_loop_stops_safely_when_model_keeps_requesting_tools`,
  `::test_loop_stops_safely_when_model_response_is_unparseable`). Commit
  `5e7f2bc`.
- **Human-reviewed:** three live execution traces were run and read in full
  (not just their status field) before being accepted as the week's
  required evidence; two further live attempts to trigger a different
  control were run, found not to exercise what was intended (the model
  self-refused before attempting the tool call), and reported honestly as
  a partial result rather than claimed as full coverage — see
  `docs/Week5_Agent_Task_Contract.md`'s "Execution traces" section.

## Week 6 — Memory & state (Alvin)

Commits `6c9761e`, `e90c87d`, `739d9c5` carry no AI-tool declaration.
**Needs Alvin's input:** which parts of `src/memory/case_history.py`,
`docs/Week6_State_Model.md`, `Week6_Memory_Design.md`,
`Week6_MCP_Interface.md` were AI-assisted.

## Week 7 — Evaluation, guardrails, failure catalogue (two attempts)

- **First attempt — Cursor (Emmanuel Okello), commit `ff99a76`.** Cursor was
  used to build the 34-scenario evaluation set, `src/guardrails.py`, and
  the failure catalogue.
- **This was caught and reverted** — commit `be87505`, itself done with
  Claude's help (declared: `Co-Authored-By: Claude Opus 5.5`). The review
  found 24 of 34 traces used **scripted model turns, not live calls**
  (latency 0 ms throughout), and the verdict column had been **pre-filled
  with PASS** — a direct violation of the rule every week of this project
  has otherwise followed (`RUNBOOK.md`: *"Never pre-fill a result... a
  fabricated result is the one thing you cannot explain when questioned"*).
  This is the single most important entry in this log: a generated
  artefact was reviewed, found to fail the project's own integrity
  standard, and discarded rather than kept because it "looked done."
- **Second attempt — commits `3bcfc67`, `2c51baf`, `ef92fe4`, `f68c18f`
  (Alvin).** Redone against a real model (Groq `openai/gpt-oss-120b`), all
  33 scenarios live, verdicts filled by hand after reading the traces.
  These commits carry no AI-tool declaration. **Needs Alvin's input:**
  whether/how AI assisted the redo, so this entry can name the tool the
  way every other entry does.

## Week 8 — Final presentation (Claude Code, Swale)

- **Built `UniFlow_Final_Presentation.pptx`** (10 slides) and
  `docs/Week8_Live_Demo_Cue_Sheet.md` to the brief's §10 structure.
- **Rehearsed, not assumed working:** all four live-demo commands were
  actually run end to end against Groq before being put in the deck or the
  cue sheet, and their real output (including an unprompted Week 6 memory
  dedup hit on the second command) shaped what the deck says rather than
  the other way around. The resulting traces were kept as the deck's
  documented backups. Human review command (`scripts/review_defect.py`)
  was also test-run and its mutation reverted before committing, since the
  real demo should flip a fresh defect, not a rehearsal one.
- **Human-reviewed:** every slide was rendered to an image and visually
  checked (text fit, contrast, no placeholder content) before being
  accepted; one design issue (accent-bar styling that reads as an
  AI-generated visual tell) was caught in that review and fixed.
- **Week 8 Guide, final report work (commit `953fe69`, Alvin)** carries no
  AI-tool declaration. **Needs Alvin's input.** -->

UniFlow, AI Engineering Log

Required by the capstone brief §6 ("Keep a concise AI Engineering Log for material AI-assisted decisions or generated artefacts") and referenced in the Final Engineering Report's AI-use declaration (brief §9, §6).

Scope. This logs material AI-assisted decisions and generated artefacts, not every autocomplete suggestion. A material entry is one where the AI either (a) produced a non-trivial artefact a reviewer would want to know was AI-drafted, or (b) changed a real engineering decision (found a bug, reverted bad evidence, chose an architecture). Each entry names the tool, what it was asked to do, what a human reviewed/changed, and why it mattered, the brief's requirement that "students remain accountable ... and must be able to explain any AI-generated artefacts" is the test every entry below is written to pass.

Tools used on this project, by name: Claude Code (Anthropic) and Cursor. Both are declared per brief §6; see the per-week entries below for which tool touched which week.

How this log was compiled. Authorship comes from the git history (git log, all 50 commits on main). Tool attribution comes from two sources: automated commit trailers, and each author's own account. Only two commits carry a tool trailer (ff99a76: Cursor; be87505: Claude Opus 5.5), so for every other commit the tool named below is the author's recollection given at the time of writing, not something recorded when the commit was made. Where an author could not itemise exactly which parts were AI-assisted, the entry says so rather than guessing. Authors are listed by git name: Alvin170803 and "Ainebyona .P. Alvin" are the same person (Ainebyona Alvin Police), MahamatAbdelrassoul is Yohana Mahamat Abdelrassoul, and Emmanuel Okello is Okello Emmanuel Odongo. The task owner in docs/Contributions.md can differ from the git author, because one member sometimes pushed another's files.

Working pattern. Work was done in pairs, two of four members per week. Alvin used Claude Code for all of his contributions. Swale used Claude Code. Emmanuel used Cursor, and Yohana mainly used Cursor with some Claude Code (both as reported by Alvin, to be confirmed by each).

Week 1: Charter, user stories, boundary matrix, architecture description

Git authors: Swale (bcc6138, e044cb8). The Week 1 documents are Word files owned by all four members (see docs/Contributions.md). To confirm: each owner states whether AI assisted their document; if none did, this entry should say "no AI assistance" explicitly.

Week 2: Claude Code (Swale, Alvin)
Harness bugs found and fixed, not just features added. While running the Week 2 evaluation, Claude Code found that baseline.py never passed the real story_id into the prompt (the model had to guess it), that REQUIRED_CASE_FIELDS didn't actually enforce the rule_source field the output contract declared required, and that eval_runner.py --case silently overwrote the results CSV for every other case. All three were reviewed, fixed, and covered by new tests in the same session, see prompts/PROMPT_CHANGELOG.md and commit e7ed6e8.
Prompt v1.1 built from confirmed v1.0 failures only. One hypothesised change from the original scaffold (bare-JSON enforcement) was reviewed against the actual trace evidence, found unnecessary (10/10 traces were already clean JSON, the API layer already enforced it), and deliberately dropped rather than kept for its own sake. Reasoning recorded in prompts/qa_test_designer_v1.1.md §0.
Human-reviewed: every verdict in eval/results_v1.0.csv / results_v1.1.csv was scored by reading the actual model output against the case's expected list, not auto-assigned.
Alvin, Claude Code (a49aaf3, 644dd64, aa09003, d9eccda): the 10-case evaluation table, the Week 2 progress report, and small edits to the playbook and model setting. Claude Code assisted; Alvin cannot itemise every part. The verdicts in the evaluation table are covered by the human-review bullet above.
Week 3: RAG (Alvin, Emmanuel)
Alvin, Claude Code (87cabf7, e6defb0, d22fec7, 8500801, 607fb5a): pushed the RAG pipeline in src/rag/, the architecture note docs/Week3_RAG_Architecture.md, the 15-case RAG evaluation results, the Week 3 failure analysis and progress report, and two knowledge-base edits (an extra programme business rule; CAED programmes are all four years). Claude Code assisted across this work; the exact split between human and AI-written parts was not recorded.
Human-reviewed: the RAG evaluation verdicts and the four-mechanism failure analysis (docs/Week3_Failures.md) were read from the retrieved chunks and traces, not auto-assigned. The two knowledge-base edits are content decisions made by Alvin.
To confirm (Emmanuel): docs/Contributions.md lists him as owner of the RAG pipeline; which tool, if any, he used for it.
Week 4: Tools (Alvin, Yohana)
Alvin, Claude Code (89e9e2d, ee362d7, 2aede9d, c269858): the Tool Catalogue (docs/Week4_Tool_Catalogue.md), the defects evidence file and further evidence traces. Claude Code assisted; not itemised.
Yohana (git name MahamatAbdelrassoul), mainly Cursor with some Claude Code, per Alvin (ff91be9, d4219b1, 66e09fe, f6bf635): tool calling in src/tools/ and src/tool_baseline.py, the 15-case tool evaluation traces, the Week 4 report and the project README. To confirm (Yohana): which of these artefacts came from which tool, and what she changed before committing.
Human-reviewed: the Week 4 evaluation tested the deterministic controls (allow-list, argument checks, error handling) without a live model, and was reported as such; Week 7 re-ran the misuse scenarios live.
Week 5: Bounded agent loop (Claude Code, Swale; Alvin)
Extended the Week 4 loop into an explicit Sense→Plan→Act→Observe→Stop agent, per docs/Week5_Agent_Task_Contract.md (written before the code changes, not after, so the contract wasn't rationalising whatever the code happened to do).
Found and fixed a real latent bug, not a hypothetical one: a tool_call arriving on the last allowed round previously fell through to an unenforced continue in live mode, so handle_request() could return parsed_output: None if the model never volunteered a terminal status. Caught by reasoning through what "stop safely" must guarantee, not by an existing test, no prior test or eval case had ever driven the loop that far. Fixed, and two new regression tests added (tests/test_tools.py::test_loop_stops_safely_when_model_keeps_requesting_tools, ::test_loop_stops_safely_when_model_response_is_unparseable). Commit 5e7f2bc.
Human-reviewed: three live execution traces were run and read in full (not just their status field) before being accepted as the week's required evidence; two further live attempts to trigger a different control were run, found not to exercise what was intended (the model self-refused before attempting the tool call), and reported honestly as a partial result rather than claimed as full coverage, see docs/Week5_Agent_Task_Contract.md's "Execution traces" section.
Alvin, Claude Code (739d9c5, report updates for Weeks 5 and 6): the agent task contract and the Week 5 report. Claude Code assisted; not itemised.
Week 6: Memory and state (Alvin, Swale)
Alvin, Claude Code (6c9761e, e90c87d, 739d9c5): pushed the Week 6 deliverables, including src/memory/case_history.py, the state model (docs/Week6_State_Model.md), the memory design note, the MCP-style interface spec and the Week 6 report. Claude Code assisted across these; the exact split was not recorded. docs/Contributions.md names Swale as owner of the working memory module and Alvin as owner of the state model.
Human-reviewed: memory behaviour was checked with dedicated tests (tests/test_memory.py) and demonstration traces. Week 6 also found that shared memory would have silently changed a Week 4 evaluation result, so evaluation runs use isolated, reset memory.
To confirm (Swale): which tool he used for the memory module.
Week 7: Evaluation, guardrails, failure catalogue (two attempts)
First attempt, Cursor (Emmanuel Okello), commit ff99a76. Cursor was used to build the 34-scenario evaluation set, src/guardrails.py, and the failure catalogue.
This was caught and reverted, commit be87505, itself done with Claude's help (declared: Co-Authored-By: Claude Opus 5.5). The review found 24 of 34 traces used scripted model turns, not live calls (latency 0 ms throughout), and the verdict column had been pre-filled with PASS, a direct violation of the rule every week of this project has otherwise followed (RUNBOOK.md: "Never pre-fill a result... a fabricated result is the one thing you cannot explain when questioned"). This is the single most important entry in this log: a generated artefact was reviewed, found to fail the project's own integrity standard, and discarded rather than kept because it "looked done."
Second attempt, commits 3bcfc67, 2c51baf, ef92fe4, f68c18f (Alvin). Redone against a real model (Groq openai/gpt-oss-120b), all 33 scenarios live, verdicts filled by hand after reading the traces. Alvin used Claude Code for the redo. The prompts, the 33 scenarios and every verdict were then read and assigned by hand against the traces; no verdict was auto-filled. The revert commit itself carries the trailer Co-Authored-By: Claude Opus 5.5.
Week 8: Final presentation, release and report (Claude Code, Swale; Alvin; Yohana)
Built UniFlow_Final_Presentation.pptx (10 slides) and docs/Week8_Live_Demo_Cue_Sheet.md to the brief's §10 structure.
Rehearsed, not assumed working: all four live-demo commands were actually run end to end against Groq before being put in the deck or the cue sheet, and their real output (including an unprompted Week 6 memory dedup hit on the second command) shaped what the deck says rather than the other way around. The resulting traces were kept as the deck's documented backups. Human review command (scripts/review_defect.py) was also test-run and its mutation reverted before committing, since the real demo should flip a fresh defect, not a rehearsal one.
Human-reviewed: every slide was rendered to an image and visually checked (text fit, contrast, no placeholder content) before being accepted; one design issue (accent-bar styling that reads as an AI-generated visual tell) was caught in that review and fixed.
Alvin, Claude Code (953fe69, eb73b8b): release notes, the first draft of the Final Engineering Report, and live-demo testing. The demo testing changed src/tools/dispatch.py and added a test in tests/test_tools.py, and the new traces and defect file came from real Groq runs. Claude Code assisted; not itemised.
Final report assembly, Alvin, Claude (chat): merging the screenshot figures, the contributions appendix table and the placeholder clean-up into the report. Alvin checked each placeholder and number against the repository and evidence files before accepting it.
Yohana (31fe3df): the contribution record and ClickUp board screenshots. 

