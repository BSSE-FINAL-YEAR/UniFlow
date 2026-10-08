# UniFlow — Week 6 MCP-Style Interface Specification

Week 6 offers a choice: implement a real external integration, or document
an existing capability as an MCP-style interface. This project chooses the
latter — see the reasoning below — and specifies `check_course_load`
(Week 4's read-only tool) as it would be exposed by a UniFlow MCP server.

**Scope note, per the brief's own reading note:** the three assigned
textbooks do not cover the Model Context Protocol in the editions supplied,
so this is written from general, publicly available knowledge of MCP's
shape (a server exposes named tools with a JSON Schema input, a client
invokes them, results come back as structured content) rather than from
assigned course material. The wire-level JSON-RPC framing below is
illustrative of that shape, not a claim of exact conformance to one SDK
version — the parts that matter for grading (capability, inputs, outputs,
permissions, security boundary) do not depend on that framing being exact.

## Why document, not implement

This team has logged API-key instability in three separate progress
reports (Weeks 2, 4, 5) and has consistently chosen the lower-dependency
option at every prior fork in the road: BM25 over embeddings (Week 3),
manual JSON-dispatch over native provider function-calling (Week 4). Adding
a live external MCP server under the same time pressure, with the same
track record of external-dependency flakiness, would risk the newest,
least-tested part of the stack being the one most likely to fail during a
demo. Documenting an existing, already-tested capability costs no new
dependency and produces the same graded artifact the activity asks for: a
specification covering capability, inputs, outputs, permissions and
security boundary.

## The capability: `check_course_load`

If UniFlow exposed its tools over MCP instead of the in-process manual
dispatch it uses today, a client (an IDE, another agent, a different
orchestrator entirely) would see this tool advertised by a UniFlow MCP
server:

```json
{
  "name": "check_course_load",
  "description": "Check whether a proposed course load (year of study and units requested) is within UniFlow's approved R-04 limit. Read-only; does not modify any record.",
  "inputSchema": {
    "type": "object",
    "required": ["year_of_study", "units_requested"],
    "properties": {
      "year_of_study": {"type": "integer", "minimum": 1, "maximum": 4},
      "units_requested": {"type": "integer", "minimum": 0}
    }
  }
}
```

This is identical to the input schema already in
`docs/Week4_Tool_Catalogue.md` — MCP does not ask for a different contract,
it asks for the same contract to be *discoverable* by a client that has
never seen UniFlow's code, rather than hard-coded into one project's system
prompt the way `src/tool_baseline.py`'s `OUTPUT_CONTRACT` string does today.

### Inputs

As above: `year_of_study` (1-4), `units_requested` (>= 0). No student
identifier, no free-text field, no optional parameters — the smallest
input that answers the question, same rationale as the Week 4 catalogue's
"design note on authorization by scope."

### Outputs

A client calling this tool over MCP would receive a result equivalent to:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"ok\": false, \"rule\": \"R-04\", \"message\": \"Course load 6 exceeds Year 3 maximum of 5\", \"value\": null}"
    }
  ],
  "isError": false
}
```

`isError` reflects whether the *tool call itself* failed (a malformed
request, a crashed server) — it is `false` here even when `ok: false`,
because "the load is not allowed" is a successful, correctly-answered
call, exactly as it already is in `src/tools/check_course_load.py`'s
`output_is_valid()`. The embedded JSON is UniFlow's own existing output
schema, unchanged — MCP wraps it, it does not replace it.

### Permissions

- No authentication token or API key is required to call this tool — it
  is read-only and has no side effect, matching the Week 4 catalogue's
  "the agent may call this freely and always."
- A real MCP deployment would still gate this at the **client** level:
  whichever host application connects to the UniFlow MCP server decides
  whether a given user/session may invoke tools on it at all. UniFlow's
  own allow-list (`src/tools/registry.py`) remains the second, independent
  layer underneath that — a client being permitted to talk to the server
  does not bypass the server's own authorization logic.

### Security boundary

- **Process boundary.** In this prototype, `check_course_load` runs
  in-process, called directly by `src/tools/dispatch.py` — there is no
  separate server process and no network exposure. An MCP version would
  run as its own process (stdio or HTTP transport), which is a stronger
  boundary than today's in-process call, not a weaker one: a crash or
  compromise of the tool server cannot directly touch the orchestrator's
  memory space.
- **Data boundary.** The tool can read `uniflow_core.rules`'s fixed limit
  table. It has no filesystem access beyond that, no network access, and
  no ability to write anything — there is nothing in this tool's
  implementation that could be used to exfiltrate or modify data even if
  the arguments were adversarially crafted, because there is no write path
  at all.
- **What this tool cannot become a vector for.** It cannot be used to
  reach `create_defect_report`, `scripts/review_defect.py`, or any other
  UniFlow capability — an MCP client sees exactly one tool, with exactly
  one input shape, and nothing in its implementation can escalate to
  another action. This mirrors the Week 1 Boundary Matrix's allow-listing
  principle at the interface level, not just the orchestration level.

## What would change if this were implemented live

A real UniFlow MCP server would need: a server process (likely Python,
wrapping the existing `src/tools/` modules with no logic changes), a
transport choice (stdio for a local client, HTTP/SSE for a remote one), and
a decision about whether `create_defect_report` is exposed over the same
server (if so, its "no `status` field" authorization-by-omission design
from the Week 4 catalogue carries over unchanged — MCP does not require
revisiting that control, it just adds a second place the schema is
enforced: client-side validation against the advertised `inputSchema`, in
addition to `dispatch()`'s own server-side check). None of this was built
this week, per the "document, not implement" decision above.
