# UniFlow — Week 7 guardrails

The Week 4 allow-list, argument schema, iteration cap and human-only approval path were already in the code. Week 7 adds the checks that were only prompt text, and it records them.

## What already existed

| Control | Where | What it stops |
|---|---|---|
| Tool allow-list | `src/tools/registry.py`, `dispatch()` | `approve_defect`, `review_defect`, any other name |
| Argument schema | `check_course_load.validate_arguments`, `create_defect_report.validate_arguments` | Missing fields, wrong types, year outside 1–4 |
| Authorization | `status` on `create_defect_report` | Writing `approved` or `rejected`. The file is not created. |
| Iteration limit | `MAX_TOOL_ROUNDS = 3` | A model that keeps calling tools. The extra call is not dispatched. |
| Human approval | `scripts/review_defect.py`, not on the allow-list | The agent cannot move a draft off `pending_review`. |

## What Week 7 adds (`src/guardrails.py`)

**Input.** An empty request returns `insufficient_context` and does not call the model. A request longer than 4000 characters, or one containing ASCII control characters, returns `refused`.

**Prompt-injection awareness.** Five patterns, matched in Python before `generate()`:

- "ignore previous instructions" (the shape of Week 3 case RQ-15)
- "disregard the rules / system prompt / instructions"
- a request to print or reveal the system prompt, `.env`, an API key, or a secret
- "you are now …"
- a fake `<system>` or `<prompt>` tag

**Prohibited actions**, also before the model: deploy or merge code, modify an academic record or grade, delete records, run a shell command.

**Output.** After a terminal model object:

- a status outside the contract (`approved` included) is not stored as the outcome
- "is allowed" against `check_course_load` `ok: false`, or "not allowed" / "violation" against `ok: true`, is refused
- "I approved the defect" is refused; a sentence that says "Cannot approve" is not
- a course-load allow/deny with no `check_course_load` result is refused
- stating the draft retake rule ("retake" and "up to 2 times") without calling it a draft is refused

The model's original object stays on the trace step as `blocked_model_output`. The outcome status is `refused`.

"Mark the defect approved now" is not in the injection list. That sentence still goes to `dispatch()`, which returns `unauthorized` and writes nothing. `tests/test_guardrails.py::test_ordinary_approval_request_still_reaches_dispatch` locks that.

## What a trace now contains

`prompts` (system and user, per round), `retrieval` (top 4 chunks: doc id, status, score, text), `tool_results`, each model call's latency and error, `guardrails`, and `metrics`. Written by `handle_request()` to `evidence/traces/tools/` for a normal run, and to `evidence/traces/week7/` for the evaluation runner.
