# UniFlow — Week 2 Playbook

**BSE4104 Emerging Trends in Software Engineering | Group I**
**Week 2 (7–11 Sept 2026): Foundation-Model Engineering and Prompting**

---

## 0. The reframe that unblocks this week

UniFlow (the System Under Test) does not exist yet. That is fine, and this week is **not** the week to build it.

Week 2's weekly focus, verbatim from the brief:

> "Build the smallest useful model-backed capability and establish a tested baseline before adding RAG or agents."

For an AI-native **QA Agent**, the smallest useful model-backed capability is:

> **Given a user story + its acceptance criteria + the UniFlow business rules, generate a structured, executable-shaped set of test cases — and refuse when the request falls outside approved scope.**

This is the correct Week 2 slice for three reasons:

1. **It needs no running SUT.** Its inputs are the Week 1 artifacts you already wrote — the 12 user stories, the acceptance criteria, and the rule table from the Project Charter.
2. **It is the QA Agent's actual first capability.** US-11 says "the agent generates tests linked to the selected workflow/rules." You are building exactly that, minus execution (which is Week 4's tool-calling work).
3. **It produces a testable baseline.** Test-case generation has a strict output contract (JSON), so pass/fail is objective — which is what makes a 10-case evaluation table meaningful rather than vibes.

**What you do NOT do this week:** build the frontend, build the database, build the timetable engine, or execute any tests. Execution arrives in Week 4 through approved tools.

**Small hedge for Week 3–4:** one member builds a *rules-only* UniFlow core — the business rules from the charter as pure functions, plus a small synthetic dataset. No UI, no DB, no API. About 150 lines. That becomes the thing tests actually run against in Week 4, and it doubles as part of the Week 3 corpus.

---

## 1. Timing reality

Week 2 ends **Friday 11 September 2026**. It is Thursday afternoon. Plan accordingly:

| Block | When | What |
|---|---|---|
| **A — Parallel build** | Thu 10 Sept, evening | All four members work independently. No one waits on anyone except for the API key. |
| **B — Integration** | Fri 11 Sept, morning | Wire prompt + client + runner. Run the 10 cases against v1.0, then v1.1. |
| **C — Write-up & submit** | Fri 11 Sept, afternoon | Fill in actual results, finalise the report, push, log ClickUp evidence. |

**The single critical-path item is the API key.** If Swale cannot get a working key tonight, everything downstream slips. Get that done first, in the next hour.

---

## 2. Deliverable → owner map

| # | Deliverable | Owner | Week 1 role |
|---|---|---|---|
| D1 | Working baseline model interaction | **Odongo Emmanuel** | Backend / System Lead |
| D2 | Model Selection Note (1 page max) | **Swale Sebabe** | AI / Agent Lead |
| D3 | Prompt Specification + version history | **Yohana Mahamat** | Project / Requirements Lead |
| D4 | 10-case prompt evaluation table | **Ainebyona Alvin (EMUDUKO)** | QA / Testing & Documentation Lead |
| D5 | Week 2 progress report (1–2 pages) | **Ainebyona Alvin (EMUDUKO)** | QA / Testing & Documentation Lead |

Roles carry over cleanly from Week 1, which is good — the brief says "Every member must own identifiable tasks per each week."

**Load balance note.** D1 and D2 are naturally paired (the client wrapper is small; the note is analysis). D4 and D5 are the heaviest single load, which is why EMUDUKO gets no build task. D3 is medium but on the critical path for D4. Roughly even.

---

## 3. Dependency graph

```
Swale: get API key ──┐
                     ├──> Odongo: llm_client.py works ──┐
Swale: Model Note ───┘                                  │
                                                        ├──> EMUDUKO: run 10 cases ──> D4 table
Yohana: Prompt Spec v1.0 ───────────────────────────────┘                                │
   │                                                                                     │
   └──> Yohana: v1.1 (informed by first eval results) ──> re-run ──> D4 comparison ───────┤
                                                                                         │
Odongo: uniflow_core rules (independent, no blocker) ────────────────────────────────────┤
                                                                                         v
                                                                            EMUDUKO: D5 progress report
```

**Two things can start immediately with zero dependencies:**
- EMUDUKO designing the 10 cases (inputs and expected behaviour don't need a working model)
- Odongo writing `uniflow_core/rules.py` from the charter rule table

---

## 4. Per-member briefs

### 4.1 Swale Sebabe — AI / Agent Lead
**Owns: D2 (Model Selection Note), and the API access that unblocks D1**

**Tonight, in this order:**

1. **Get a working API key — do this first, before writing anything.**
   - Primary: Google AI Studio (Gemini). Free tier, no credit card, works from Uganda.
   - Fallback: Groq. Free tier, no card, very fast, open-weight models.
   - Have a fallback key even if the primary works. A dead key on Friday morning kills the week.
2. **Measure, don't guess.** Run 5 identical calls and record actual latency from Kampala. The brief asks you to document "capability, cost, latency, privacy and access considerations" — measured numbers are what separate a good note from a generic one. `src/measure_latency.py` in the starter bundle does this for you.
3. **Write the note (1 page MAX — it is a hard cap).**

**Model Selection Note structure:**

| Section | Content | Length |
|---|---|---|
| Decision | One sentence: which model, for what. | 1 line |
| Options considered | 3–4 rows: model, access, cost, context window, notes. | Table |
| Capability fit | Why this model suits *structured test-case generation* specifically — JSON adherence, instruction following, reasoning over rules. Not general benchmarks. | 3–4 lines |
| Cost | Free-tier limits and what happens at the ceiling. Estimate your Week 7 load: 30 scenarios × ~5 re-runs × ~2k tokens. | 3 lines |
| Latency | Your **measured** median and p95 from Kampala. Note that this matters more for a Week 5 agent loop, where one task = many calls. | 2–3 lines |
| Privacy & access | Critical for you: UniFlow uses **synthetic data only** (Week 1 scope exclusion), so no real student data leaves the country. State this explicitly — it maps to the brief's integrity rule about not sending restricted data to external services. Note free-tier data-retention terms. | 3–4 lines |
| Risks & fallback | Rate limits, deprecation, outage → named fallback model and how you'd switch (one env var). | 2 lines |

⚠️ **Verify every number against official docs before submitting.** The brief explicitly says "Verify all AI-suggested references and technical claims before using them." Free-tier limits change often; do not cite a blog post. Cite `ai.google.dev/pricing` or `console.groq.com/docs/rate-limits` and date the citation.

**Reading:** Lanham Ch.2, "Choosing the optimal LLM," pp. 34–36. Osmani Ch.1, "AI Models: The Landscape for Code Generation," pp. 25–30.

---

### 4.2 Odongo Emmanuel — Backend / System Lead
**Owns: D1 (Working baseline model interaction) + the rules-only UniFlow core**

**Tonight:**

1. **Set up the repo structure** exactly as the brief specifies (`docs/`, `prompts/`, `src/`, `tests/`, `evidence/`, `knowledge/`, `.env.example`). Marks are attached to this. Commit `.env.example`; **never** commit `.env`.
2. **`src/llm_client.py`** — thin provider wrapper. One function, `generate(prompt, system)`. Must handle: timeout, retry with backoff, rate-limit error, and provider switch via `LLM_PROVIDER` env var. Keep it boring.
3. **`src/baseline.py`** — the actual baseline interaction. Loads a prompt version from `prompts/`, injects a user story + rules, calls the client, validates the response is well-formed JSON against the expected schema, writes a full trace to `evidence/traces/`.
   - **The trace is a graded artifact, not a nice-to-have.** Every run must record: prompt version, model, input, raw output, parsed output, latency, token counts, timestamp. Week 7 asks for observability evidence; starting the habit now means you get it free.
4. **`src/uniflow_core/rules.py`** — the charter rules as pure functions. This is the hedge for Week 3–4.
   - `validate_registration_number(reg_no)` → derives student number, checks format
   - `check_course_load(year, units)` → Y1:6, Y2:6, Y3:5, Y4:4
   - `check_teaching_window(mode, start, end)` → PS 08:00–16:00, EVE 16:30–20:30
   - `check_course_frequency(count_per_week)` → ≥1 and ≤2
   - `check_duplicate_student_number(...)`, `check_prerequisites(...)`
   - Plus `data/seed.json` with ~10 synthetic students, ~10 courses, a few programmes.

**Do NOT build:** frontend, database, REST API, timetable solver. Not this week.

**Definition of done:** `python src/baseline.py --story US-08 --prompt v1.0` prints valid JSON test cases and drops a trace file.

---

### 4.3 Yohana Mahamat — Project / Requirements Lead
**Owns: D3 (Prompt Specification + version history)**

This is the intellectual core of Week 2 and the most commonly under-done deliverable. A prompt spec is **not** "here is my prompt." It is a specification with six named parts, which the brief lists explicitly: *role, task, context, constraints, output format, failure behaviour.*

**Tonight:**

1. **Extract the rule pack.** Pull the rule table from the Week 1 Project Charter into `prompts/context/uniflow_rules.md`. Mark each rule as *source-derived* or *UniFlow Business Rule* — your charter already makes that distinction, and preserving it here proves the model is grounded in approved requirements rather than inventing rules. This is your bridge into Week 3's RAG work.
2. **Write `prompts/qa_test_designer_v1.0.md`.** Use the starter in this bundle. Every section must be present and labelled.
3. **After the first eval run, write v1.1** — and this is the part that earns the marks. The brief requires "at least two **meaningful** prompt iterations." Meaningful means: *a failure was observed in the evaluation table, and the prompt change targets that failure.*
   - Bad iteration: "made the wording clearer."
   - Good iteration: "v1.0 produced prose preamble before the JSON in 4/10 cases (PE-02, PE-04, PE-05, PE-09). v1.1 adds an explicit output-only constraint plus one few-shot example of a bare JSON response. Re-run: 0/10 preamble failures."
4. **Maintain `prompts/PROMPT_CHANGELOG.md`** — version, date, author, what changed, why (linked to an eval case ID), observed effect. Git history alone is not enough; the brief wants "evidence of meaningful changes."

**Techniques worth deliberately naming in the spec** (from Lanham Ch.2, pp. 25–34 and Osmani Ch.2, pp. 40–63) — using named techniques and citing them is exactly what an "Emerging Trends" marker is looking for:

| Technique | How it applies here |
|---|---|
| **Role / persona prompting** | "You are a QA test designer for a university academic-management system." |
| **Clear, specific instructions** | Enumerate coverage requirements rather than "write good tests." |
| **Providing reference text** | Inject the approved rule pack; forbid the model from using rules not in it. |
| **Splitting complex tasks** | One user story per call, not all 12 at once. |
| **Structured output / schema** | Strict JSON schema; makes evaluation objective. |
| **Few-shot examples** | One worked example in v1.1 to fix format drift. |
| **Giving the model time to reason** | Optional `reasoning` field before `test_cases`, or explicit step ordering. |
| **Explicit failure behaviour** | `{"status": "insufficient_context", "reason": "..."}` instead of guessing. |

**Failure behaviour is where most groups lose marks.** Your Week 1 Core Guardrails already promise "safe failure: when evidence is insufficient, the agent should report uncertainty or request human review rather than invent an answer." The prompt spec must operationalise that promise, and cases PE-06, PE-07 and PE-10 in the evaluation table exist specifically to test it.

---

### 4.4 Ainebyona Alvin (EMUDUKO) — QA / Testing & Documentation Lead
**Owns: D4 (10-case evaluation table) + D5 (Week 2 progress report)**

Both drafted for you in this bundle. Your work is:

**Tonight (no dependencies — start now):**
1. Review the 10 designed cases. Confirm each maps to a real Week 1 user story or a real scope exclusion. Adjust any you disagree with.
2. Confirm the scoring rubric with the team so the verdicts aren't subjective.

**Friday morning (after Odongo's runner works):**
3. Run all 10 cases against **v1.0**. Record actual behaviour verbatim. Save raw outputs to `evidence/traces/v1.0/`.
4. Hand the failure list to Yohana so v1.1 targets real observed problems.
5. Re-run all 10 against **v1.1**. Record the delta.
6. Fill the Actual / Verdict columns and write the findings summary.

**Friday afternoon:**
7. Finalise D5 with real numbers, real challenges, real commit links.
8. Log every Week 2 task in ClickUp with owner, status, due date, and link each to a commit. Capture screenshots into `evidence/screenshots/`.

⚠️ **Do not pre-fill results.** The Actual and Verdict columns stay empty until the runs happen. Fabricated results are the fastest way to fail the "every student must explain their work" rule at the demo.

---

## 5. What "done" looks like Friday evening

- [ ] `prompts/qa_test_designer_v1.0.md` and `v1.1.md` committed, both used in real runs
- [ ] `prompts/PROMPT_CHANGELOG.md` explains v1.0 → v1.1 with an eval case ID as justification
- [ ] `python src/baseline.py` runs end-to-end and produces valid JSON
- [ ] ≥20 trace files in `evidence/traces/` (10 cases × 2 prompt versions)
- [ ] Model Selection Note ≤ 1 page, with measured latency and cited official sources
- [ ] Evaluation table with all 10 Actual + Verdict cells filled, plus v1.0 vs v1.1 comparison
- [ ] Week 2 progress report, 1–2 pages, with GitHub and ClickUp links
- [ ] ClickUp: all Week 2 tasks logged, assigned, closed
- [ ] Every member can explain the whole week, not just their part

---

## 6. Three traps to avoid

**1. Building UniFlow instead of the model capability.** The most likely failure mode this week. The brief rewards "smallest useful," and the SUT is not a Week 2 deliverable. Resist it.

**2. Cosmetic prompt iterations.** v1.0 → v1.1 must be driven by an observed failure with a case ID attached. Anything else reads as box-ticking.

**3. A 10-case table that is all happy paths.** Your Week 1 AI Boundary Matrix is unusually strong — it lists a dozen things the agent may *not* do. The evaluation table is where you prove those boundaries actually hold under a real model. Roughly half the cases should be edge, unsupported or adversarial. The designed set below is 4 normal/edge, 3 unsupported, 3 adversarial/stress.

---

## 7. Week 2 required reading (split it)

| Member | Reading |
|---|---|
| Swale | Lanham Ch.2 "Choosing the optimal LLM" pp. 34–36; Osmani Ch.1 pp. 25–30 |
| Yohana | Lanham Ch.2 "Prompting LLMs with prompt engineering" pp. 25–34; Osmani Ch.2 pp. 40–63 |
| Odongo | Huyen Ch.5 prompting basics and best practices, pp. 212–235 |
| EMUDUKO | Huyen Ch.2 "The Probabilistic Nature of AI" pp. 105–111 — directly relevant to why you run each case more than once |

Each person contributes 2–3 lines to the progress report's "key engineering decisions" section citing their reading. Cheap marks, and it makes the report defensible under questioning.
