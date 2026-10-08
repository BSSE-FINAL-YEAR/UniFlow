# UniFlow — Week 6 Memory Design and Data Handling Note

## The use case

**Duplicate-defect case history.** If the agent detects the same rule
violation for the same story more than once (e.g. `check_course_load`
flags a Year 3 / 6-unit registration today, and the identical request
arrives again next week), it should not file a second, near-identical
`pending_review` defect report. It should recognize the violation has
already been reported and say so.

This was chosen over the two alternatives considered (see the earlier
discussion before this week's code was written):
- *Approved preference memory* (remembering a human reviewer's past
  approve/reject decision) — rejected because it risks memory starting to
  look like it influences a decision that must stay human-only.
- *Prior task-result cache* (caching `check_course_load` results) —
  rejected because the tool is already free, instant and deterministic;
  caching it has no real benefit and would be memory added for its own
  sake rather than a justified need.

Case history is the one genuinely justified case: it improves a real QA
workflow (reviewers don't want ten copies of the same finding) and the
risk of it quietly doing something it shouldn't is easy to design out —
see "What memory does NOT do," below.

## What is stored

One JSON object per `(rule_id, story_id)` pair, in
`data/memory/case_history.json`:

```json
{
  "R-04:US-08": {
    "rule_id": "R-04",
    "story_id": "US-08",
    "defect_id": "DEF-20261008T130256",
    "path": "evidence/defects/DEF-20261008T130256.json",
    "first_seen": "2026-10-08T13:02:56Z",
    "last_seen": "2026-10-08T13:02:56Z",
    "times_seen": 1
  }
}
```

No student identifier, no free-text description, no severity — only enough
to answer "has this exact violation already been filed, and under what
defect_id." This is deliberate: the full detail already lives in the
defect file itself (`evidence/defects/<id>.json`); memory only needs a
pointer to it, not a second copy of the content, which would be one more
place for the two to drift apart.

## Why it is stored

So the same reviewer workflow error this project has guarded against
since Week 2 (silently inventing or duplicating something that should have
a single source of truth) does not recur one layer up, in defect-report
volume instead of rule content. A reviewer queue with five duplicate
reports of the same violation is noisy and erodes trust in the reports
that follow it.

## Who can access it

- **The agent**, through `src/tools/dispatch.py` only — `find_prior_defect()`
  is consulted automatically before `create_defect_report` writes anything,
  and `remember_defect()` is called automatically right after a genuinely
  new write succeeds. The agent has no direct read/write access to the file
  outside this one call path, and no tool exposes `forget()` to the model.
- **Humans**, the same way they already access `evidence/defects/` — by
  opening the plain JSON file in the repository. No separate API or access
  control exists yet; this is a single-machine prototype with no real
  student data in it, so the Week 1 scope exclusions already cover the
  privacy question (synthetic data only).

## What memory does NOT do

This is the most important paragraph in this note, because the activity
list specifically asks to demonstrate memory helping "without silently
controlling critical decisions":

- Memory never decides whether something is a rule violation.
  `check_course_load` / R-04 is the only source of truth for that, exactly
  as it was in Weeks 4-5. A prior case-history entry cannot make a
  compliant registration look non-compliant or vice versa.
- Memory never prevents the agent from recognizing or reporting a
  violation. The agent still decides, every time, whether a violation is
  worth flagging. Memory only intercepts the *write* once that decision has
  already been made for a second time about the same thing — and even
  then, it tells the agent (and, through it, the human) that this happened,
  via `duplicate_of` and a `note` field in the tool result. It is never
  silent about having acted.
- Memory never grants, removes, or changes an authorization. `create_defect_report`
  still can only ever write `status: "pending_review"`; a duplicate result
  reports whatever status the existing record actually has. Approving or
  rejecting a defect is still exclusively `scripts/review_defect.py`, run by
  a human, unreachable by the agent — unchanged from Weeks 4-5.

## Retention and deletion

This is a prototype with synthetic data only, so there is no regulatory
retention clock to meet — but the policy is still concrete, not "indefinite
and unmanaged":

- An entry's lifetime is tied to the defect file it points to. If
  `evidence/defects/<id>.json` is ever deleted, the matching case-history
  entry should be deleted too, using `src/memory/case_history.py::forget(rule_id, story_id)`
  — implemented and tested (`tests/test_memory.py`), even though no CLI
  wraps it yet (there was no need to build one for a single-command
  operation during the prototype).
- A corrupt or unreadable store is treated as empty rather than crashing
  the agent (`_load()`'s `except json.JSONDecodeError`) — the next
  successful write repairs the file. This is a correctness safeguard, not
  a retention policy, but it means a damaged file never blocks the agent
  from continuing to work; it just loses the deduplication benefit until
  a fresh entry is written.
- `eval/_tool_eval_memory_store.json` (used only by `src/tool_eval_runner.py`)
  is deleted and rebuilt on every run and is gitignored — it is scratch
  state for one evaluation suite, not part of the deliverable.

## Where to see it work

Two real traces, same request, run back to back through the actual
`handle_request() -> dispatch() -> create_defect_report -> case_history`
path (scripted model turns — no live API key is available in this
environment; see §7 of the progress report. Re-running this live is a
cheap follow-up with a working key):

| Trace | What it shows |
|---|---|
| `evidence/traces/tools/20261008T130552_..._week6-memory-demo-first-detection.json` | First time this violation (R-04/US-08) is seen. `check_course_load` confirms the violation, `create_defect_report` writes a genuinely new file, `data/memory/case_history.json` gains its first entry (`times_seen: 1`). |
| `evidence/traces/tools/20261008T130552_..._week6-memory-demo-duplicate-detection.json` | Identical request run again. The agent still independently decides to call `create_defect_report` (nothing hid the violation from it) — but `dispatch()` finds the prior entry, returns `duplicate_of` pointing at the first run's `defect_id`, and writes no second file. `case_history.json`'s entry updates to `times_seen: 2`. |

`data/memory/case_history.json` itself, committed alongside these traces,
is the persistent evidence that survives between the two separate
`handle_request()` calls — exactly the cross-request survival
`docs/Week6_State_Model.md` says `SessionState` deliberately does not have.
