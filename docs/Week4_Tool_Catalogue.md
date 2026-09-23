# UniFlow — Week 4 Tool Catalogue

Two tools, both named in `04_Initial_Architecture_Description GROUP I.docx`
§3's "Approved Tools" row since Week 1 (`inspect_project()`-style read tool
and `create_defect_report()`). This document is the contract: written before
the orchestration code, so the two teammates implementing it in `src/tools/`
are building against a fixed spec rather than inventing one as they go.

## Shared error envelope

Both tools share one error shape for anything that isn't a normal domain
result — a missing argument, a call to a tool outside the allow-list, the
tool itself being unavailable, or a response that doesn't match its own
output schema. The orchestration layer returns this instead of calling the
underlying function, so a malformed call never reaches business logic:

```json
{
  "tool_error": "missing_parameter" | "invalid_parameter" | "unauthorized" | "unavailable" | "unexpected_response",
  "tool": "<name of the tool that was called>",
  "message": "human-readable explanation"
}
```

- `missing_parameter` — a required field is absent.
- `invalid_parameter` — present but wrong type/out of range/not in an enum.
- `unauthorized` — the model asked to call a tool not in the allow-list, or asked this tool to do something outside its authorization (e.g. asking `create_defect_report` to set `status: "approved"` directly).
- `unavailable` — the tool's own dependency failed (e.g. disk write error, `data/seed.json` unreadable).
- `unexpected_response` — the tool ran but returned something that fails its own output schema (a bug in the tool, not the caller).

This envelope is what `eval/tool_eval_cases.json` should test against for
"missing parameters / unauthorized requests / unavailable services /
unexpected tool responses" — one designed case per envelope value, per tool,
same "one trap per case" method as `RUNBOOK.md` Part B.

---

## Tool 1 — `check_course_load`

**Purpose.** Lets the agent check a specific year/units combination against
R-04 instead of reasoning about the limit in prose. Read-only — it validates
against a fixed rule table, it does not touch any student record.

**Implementation.** Already exists and is already tested:
`src/uniflow_core/rules.py::check_course_load(year_of_study, units_requested) -> Result`
(8/8 unit tests passing since Week 2, `tests/test_rules.py`). The tool
wrapper is a thin adapter from the dataclass `Result` to the JSON shape
below — it should not reimplement the limit logic.

**Input schema:**
```json
{
  "type": "object",
  "required": ["year_of_study", "units_requested"],
  "properties": {
    "year_of_study": {"type": "integer", "minimum": 1, "maximum": 4},
    "units_requested": {"type": "integer", "minimum": 0}
  }
}
```

**Output schema:**
```json
{
  "ok": true,
  "rule": "R-04",
  "message": "Course load 5 within Year 3 limit of 5",
  "value": {"limit": 5}
}
```
`value` is `null` when `ok` is `false` (the rule was violated or the year
was unsupported) — this is the underlying `Result` dataclass's own shape,
unchanged by the wrapper.

**Authorization.** Boundary Matrix row *"Course-load enforcement —
Analysis/testing only... Agent cannot approve an exception."* The agent may
call this freely and always — there is no higher-impact variant of this
tool and no approval gate, because it only reports what the rule already
says; it cannot change a student's actual registration.

**Failure behaviour:**
| Scenario | Response |
|---|---|
| `units_requested` missing | `tool_error: missing_parameter` |
| `year_of_study` is `5` or `0` | `tool_error: invalid_parameter` (schema violation) — distinct from `year_of_study: 5` being *passed through* to the function, which would instead return `ok: false` from the rule itself for an unsupported year. Test both: the schema should catch this before the function is ever called. |
| `units_requested` is `"six"` (string, not int) | `tool_error: invalid_parameter` |
| Model asks to call this for a *different* student's record it isn't authorized to view | Not applicable to this tool — it takes no student identifier, only year/units, by design (see note below) |

**Design note on authorization by scope:** this tool's input schema
deliberately has no student-identifying field. It answers "is 6 units legal
in Year 3," not "is *this student's* registration legal" — keeping it
stateless and side-effect-free avoids needing any per-student authorization
check at all. A future tool that *does* take a student identifier would need
its own authorization rule; this one doesn't need one beyond "the agent may
call it."

---

## Tool 2 — `create_defect_report`

**Purpose.** The "low-risk simulated side effect" tool. Lets the agent
record a QA finding as a draft defect report instead of describing it only
in a chat response — giving it a durable, reviewable record, per Boundary
Matrix row *"Draft defect reports — Allowed... Evidence/logs are attached or
referenced. Human reviews/accepts defects."*

**Implementation.** New — to be built in `src/tools/create_defect_report.py`
by whoever picks up orchestration. Writes one JSON file per call to
`evidence/defects/<defect_id>.json`. `defect_id` format:
`DEF-<YYYYMMDDTHHMMSS>` (timestamp-based, matching this project's existing
trace-file naming convention — no collision handling needed at this volume).

**Input schema:**
```json
{
  "type": "object",
  "required": ["story_id", "rule_id", "title", "description", "severity"],
  "properties": {
    "story_id": {"type": "string", "pattern": "^US-\\d{2}$"},
    "rule_id": {"type": "string", "pattern": "^R-\\d{2}(-[A-Z-]+)?$"},
    "title": {"type": "string", "maxLength": 120},
    "description": {"type": "string"},
    "severity": {"type": "string", "enum": ["low", "medium", "high"]}
  }
}
```
Note there is **no `status` field in the input.** That is deliberate, not an
oversight — see Authorization below.

**Output schema:**
```json
{
  "defect_id": "DEF-20260923T140501",
  "status": "pending_review",
  "path": "evidence/defects/DEF-20260923T140501.json",
  "created_at": "2026-09-23T14:05:01Z"
}
```

**Authorization.** The tool can only ever write `status: "pending_review"` —
there is no code path, and no input field, that lets a caller (model or
otherwise) set any other status. This is "authorization by omission" from
the schema itself, not a runtime check that could be argued around. Moving
a report to `"approved"` or `"rejected"` is a **separate, human-only action**
(e.g. a person edits the file, or a small `scripts/review_defect.py` run
manually — never invoked by the agent, never exposed as a tool). If a
request asks the agent to approve, close, or dismiss a defect directly,
that is `tool_error: unauthorized`.

**Failure behaviour:**
| Scenario | Response |
|---|---|
| `severity` missing | `tool_error: missing_parameter` |
| `severity: "critical"` (not in the enum) | `tool_error: invalid_parameter` |
| `story_id: "story eight"` (doesn't match `US-\d{2}`) | `tool_error: invalid_parameter` |
| Model's JSON includes `"status": "approved"` as an extra field | `tool_error: unauthorized` — the wrapper must reject an attempt to set status, not silently ignore it (silently ignoring it would hide a real attempted authorization violation from the test evidence) |
| `evidence/defects/` not writable (disk/permissions) | `tool_error: unavailable` |
| Write succeeds but the file read back doesn't match the output schema | `tool_error: unexpected_response` |

---

## Authorization traceability

| Tool | Boundary Matrix row (Week 1) | What it may do | What it may never do |
|---|---|---|---|
| `check_course_load` | Course-load enforcement — Analysis/testing only | Report whether a load is within R-04's limit | Change a student's actual registration; approve an exception |
| `create_defect_report` | Draft defect reports — Allowed; human reviews/accepts | Write a `pending_review` draft record | Set `approved`/`rejected`/any status other than `pending_review`; modify an existing defect once written |

## Orchestration note

Both tools are invoked through the manual JSON-dispatch pattern already
used by `src/rag_baseline.py` (a `"tool"` + `"arguments"` field on the
model's JSON response, validated against the schemas above before the real
function runs), not a provider-native function-calling API — see the Week 4
guidance discussion for why. The two schemas above are what get described
to the model in its system prompt, the same way `rag_baseline.py`'s output
contract is described today.
