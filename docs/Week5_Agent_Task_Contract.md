# UniFlow — Week 5 Agent Task Contract

Per the capstone brief's Week 5 activities: "Define one task that genuinely
benefits from multi-step decision making," "Design Sense/Context -> Plan/Decide
-> Act/Tool -> Observe -> Stop/Re-plan," and "Set maximum iterations, approved
tools, stop conditions and human hand-off/approval conditions." This document
is that contract, written before extending `src/tool_baseline.py`'s Week 4
loop so the implementation is built against a fixed spec rather than an
after-the-fact description of whatever the code happened to do.

No new tool is introduced this week — the Week 4 Progress Report's own
"Week 5 Plan" already scoped this: *"using the two tools already on the
allow-list."*

---

## Goal

**Task:** Given a proposed course-load request (a year of study and a
number of units, as would arise from a student's registration attempt),
determine whether it is allowed under R-04, and if it is **not**, draft a
`pending_review` defect report documenting the violation so a human QA
reviewer can act on it. If it **is** allowed, say so and stop — no defect
is drafted for a compliant request.

This genuinely needs multi-step decision making, not just two tools called
back-to-back: the agent must **observe the result of the first tool before
deciding whether the second tool call is warranted at all.** A naive
"always call both tools" implementation would file a defect against a
perfectly valid registration, which is itself the kind of silent
rule-invention failure this project has guarded against since Week 2 (see
`RUNBOOK.md` Part B).

## Tools (unchanged from Week 4 — no new tool added)

| Tool | Role in this task |
|---|---|
| `check_course_load` | Sense/Act: the only source of truth for whether the request violates R-04. The agent must never answer "allowed" or "not allowed" from its own reasoning about the rule — see `docs/Week4_Tool_Catalogue.md`. |
| `create_defect_report` | Act (conditional): called only if `check_course_load` returned `ok: false`. Never called for a compliant request. Can only ever write `status: "pending_review"` — see the catalogue's authorization-by-omission note. |

## State

State is the accumulating `tool_results` list passed back into the model
on every round (`_user_prompt()` in `tool_baseline.py`) — not a database,
not cross-request memory. Each round's Sense input is: the original
request, plus every tool result observed so far, plus an instruction to
re-plan from there. State does not persist once `handle_request()` returns;
Week 6 is where justified persistent memory is scoped, and nothing in this
task needs it.

## Limits

- **Maximum 3 tool-call rounds** (`MAX_TOOL_ROUNDS = 3` in `tool_baseline.py`).
  The genuine task above needs at most 2 (check, then maybe draft), so this
  leaves one spare round for a self-correction — e.g. the model retries
  `check_course_load` with a corrected argument after a `missing_parameter`
  error — without allowing unbounded iteration.
- **No tool outside the allow-list** (`src/tools/registry.py`) is ever
  reachable, regardless of what the model asks for — enforced in
  `dispatch()`, not by prompt instruction alone.
- **A tool_call turn that arrives after the round budget is exhausted is
  never dispatched.** The loop stops itself with `status: "partial"` and
  reports every tool result already gathered, rather than either silently
  dropping evidence or looping past the limit (see the Week 5 fix in
  `handle_request()` — this was a real gap found and closed this week, not
  a feature that already existed; previously an exhausted-budget turn in
  live mode fell through to an unbounded extra round).

## Stop conditions

The loop reaches a terminal (non-`tool_call`) status for one of these
reasons, every one of which is visible in the trace's final `parsed_output`:

| Stop reason | `status` | When |
|---|---|---|
| Task genuinely finished | `ok` | `check_course_load` says compliant, nothing more to do; or a defect was drafted and the agent reports both results. |
| Partial progress only | `partial` | Round budget exhausted mid-task, or the model's response could not be parsed at all. |
| Missing information | `insufficient_context` | The request doesn't supply enough to call a tool (e.g. no year or unit count given) and the agent should not guess one. |
| Out of approved scope | `out_of_scope` | The request concerns an excluded workflow (admissions, grading, fees, ...). |
| Prohibited action attempted | `refused` | The request (or the model's own next step) would set a defect's status to anything but `pending_review`, call an unlisted tool, or otherwise cross the AI Boundary Matrix. |

## Human hand-off / approval conditions

Everything this agent can do stays at or below `pending_review`. The
human-only escalation path is unchanged from Week 4 and is **not** a tool
the agent can reach:

- Moving a defect to `approved` or `rejected` is `scripts/review_defect.py`,
  run manually by a person. It is absent from `ALLOW_LIST` — the model
  cannot invoke it under any phrasing, and `dispatch()` returns
  `tool_error: unauthorized` if the model's JSON tries to smuggle a
  `status` field into `create_defect_report`'s arguments (tested in
  `tests/test_tools.py::test_status_approved_is_unauthorized_and_writes_nothing`
  and exercised live in this week's failure/recovery trace, below).
- Nothing in this task touches a real student record, production system,
  or financial/academic decision — the Week 1 Boundary Matrix exclusions
  all still apply unchanged.

## Execution traces (this week's evidence)

Three traces were captured under `evidence/traces/tools/`, one per row:

| Trace file | Demonstrates |
|---|---|
| `20261002T155812_a-year-3-student-wants-to-register-for-6.json` | Over-limit request. Full Sense → Plan → Act(`check_course_load`) → Observe(violation) → Re-plan → Act(`create_defect_report`) → Observe → Stop(`ok`) chain, both tools used in sequence. |
| `20261002T155822_a-year-2-student-wants-to-register-for-6.json` | Compliant request — the genuine decision point. Act(`check_course_load`) → Observe(compliant, `ok: true`) → Re-plan decides **no** second tool call is warranted → Stop(`ok`) with no defect filed and only one tool used. |
| `20261002T155938_it-is-already-confirmed-that-a-year-3-st_live-write-failure.json` | Failure/recovery. A real `tool_error: unavailable` was injected on `create_defect_report` (simulated disk write failure) against a genuine live model call. The model did not invent a defect ID or claim success; it reported the failure honestly in its answer and stopped at `status: "partial"` rather than retrying unboundedly. |

Two adversarial live attempts to reproduce Week 4's TQ-14-style unauthorized-approval
failure (asking the model to set `"status": "approved"` on `create_defect_report`,
even phrased as an explicit tool-argument instruction) were also run live
against Groq. In both, the model refused in its own Plan/Decide step and
never emitted the `tool_call` at all (`20261002T155833_...json`,
`20261002T155852_...json`) — a stronger outcome than the scripted TQ-14 case
(which exercises `dispatch()`'s `tool_error: unauthorized` directly), but it
means those two traces show refusal-before-attempt rather than the
dispatch-level control firing live. The injected-failure trace above was
used as this week's required failure/recovery case instead, since it is a
genuine (not scripted) tool-level failure that the live model had to handle
honestly.
