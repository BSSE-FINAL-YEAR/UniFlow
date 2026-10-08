# UniFlow — Week 6 State Model

Week 6's first activity is "model workflow/session state explicitly." This
document names and specifies the state Weeks 4-5 already produced but never
gave a formal shape to, and draws the line this week's second activity
depends on: **session state vs. persistent memory are two different things,
with different lifetimes, and this project now has one of each.**

## The two kinds of state in this system

| | Session state (`SessionState`) | Persistent memory (`case_history`) |
|---|---|---|
| Scope | One `handle_request()` call | Across all requests, indefinitely |
| Where it lives | In memory, inside the running Python process | `data/memory/case_history.json` on disk |
| Created | At the start of a request | The first time a given violation is drafted |
| Destroyed | When the function returns (after being written to a trace file) | Never automatically — see `docs/Week6_Memory_Design.md` for deletion |
| Purpose | Let the agent re-plan within one task using what it has observed so far | Let the agent recognize "I have already flagged this exact violation before" |

Before Week 6, both of these existed only informally: session state was four
loose local variables threaded through the loop body by hand
(`steps`, `tool_results`, `model_calls`, `final`), and persistent memory
did not exist at all. This document covers the first; see
`docs/Week6_Memory_Design.md` for the second.

## `SessionState` — the explicit model

Defined in `src/tool_baseline.py`:

```python
@dataclass
class SessionState:
    request: str
    tag: str = ""
    steps: list[dict]          # every model turn and every dispatch, in order
    tool_results: list[dict]   # just the dispatch outcomes — this is what
                                # gets fed back into the next round's prompt
    model_calls: list[dict]    # every raw model response, including scripted ones
    status: str = "in_progress"
    final: dict | None = None
    last_validation: dict | None = None
    started_at: str
    ended_at: str | None = None
```

**Lifecycle.** `handle_request()` constructs one `SessionState` at the top
of the loop. Each round calls exactly one of `record_model_turn()` (always)
or, if the model asked for a tool, `record_dispatch()` (Act + Observe in
the same step). `stop()` is called exactly once, when a terminal status is
reached — either because the model produced one, because the round budget
was exhausted, or because the post-loop safety net had to invent a
`"partial"` rather than return nothing. `to_trace_dict()` serializes the
whole thing into the same trace format Weeks 4-5 already wrote to
`evidence/traces/tools/`, plus one new top-level `"state"` block
(`status`, `started_at`, `ended_at`, `rounds_used`) making the session's
shape visible in every trace without having to reconstruct it from `steps`.

**What changed in behavior: nothing.** This was a refactor, not a new
capability — `steps`, `tool_results`, `model_calls` and the final answer are
exactly the values that existed before, now named and typed instead of
passed around as bare locals. All 28 existing tests
(`tests/test_rules.py`, `test_rag.py`, `test_tools.py`) pass unchanged
against the refactored code, which is the evidence that this is a
same-behavior restructuring.

**Why this, and not a bigger change.** The alternative — introducing a
cross-request session object, a conversation ID, multi-turn chat history —
was deliberately not done. Nothing in UniFlow's current tasks needs a
session that outlives one `handle_request()` call; Week 5's own task
contract already said so explicitly (*"State does not persist once
`handle_request()` returns"*). Modeling state explicitly does not mean
making it bigger than the task needs — it means making the state that
already exists inspectable and named, which is exactly what a `SessionState`
instance in every trace file now gives you.

## Where to see it

Every trace written by `src/tool_baseline.py` from this point on has a
`"state"` key. Run:

```
python src/tool_baseline.py --request "A Year 2 student wants to register 6 units."
```

and open the resulting `evidence/traces/tools/*.json` file.
