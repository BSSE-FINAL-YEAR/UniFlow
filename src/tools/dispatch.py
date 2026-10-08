"""Validate-then-call dispatcher for the Week 4 allow-list.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)
Week 6 memory wiring: see docs/Week6_Memory_Design.md.

Never guesses a missing value. Never calls a tool that is not listed.
Output is either the tool's success/domain schema or the shared error envelope.
"""

from __future__ import annotations

from pathlib import Path

from memory.case_history import find_prior_defect, remember_defect

from .create_defect_report import DefectWriteError
from .errors import is_tool_error, tool_error
from .registry import ALLOW_LIST, is_allowed


def dispatch(
    tool: str,
    arguments: dict | None,
    *,
    inject: str | None = None,
    defects_dir: Path | None = None,
    memory_store: Path | None = None,
) -> dict:
    """Run one approved tool. `inject` is only for designed failure tests.

    `memory_store` isolates the Week 6 case-history file the same way
    `defects_dir` already isolates where create_defect_report writes — pass
    a tmp_path-backed file in tests/eval runs so they never read or pollute
    the real data/memory/case_history.json (see docs/Week6_Memory_Design.md).
    """
    if not is_allowed(tool):
        return tool_error(
            "unauthorized",
            tool,
            f"{tool!r} is not on the tool allow-list. Approved tools: "
            f"{', '.join(sorted(ALLOW_LIST))}.",
        )

    if not isinstance(arguments, dict):
        return tool_error(
            "invalid_parameter",
            tool,
            "arguments must be a JSON object",
        )

    spec = ALLOW_LIST[tool]
    module = spec["module"]
    reason = module.validate_arguments(arguments)
    if reason:
        if reason.startswith("missing:"):
            fields = reason.split(":", 1)[1]
            return tool_error(
                "missing_parameter",
                tool,
                f"Missing required parameter(s): {fields}",
            )
        if reason.startswith("unauthorized:"):
            return tool_error(
                "unauthorized",
                tool,
                "create_defect_report cannot set status; drafts are always "
                "pending_review. Approving a defect is a human-only action "
                f"({reason.split(':', 1)[1]}).",
            )
        return tool_error("invalid_parameter", tool, reason.split(":", 1)[1])

    if inject == "malformed_result":
        return tool_error(
            "unexpected_response",
            tool,
            "Tool returned a result that failed its output schema "
            "(injected malformed_result for evaluation).",
        )

    if tool == "create_defect_report":
        prior = find_prior_defect(arguments["rule_id"], arguments["story_id"], store=memory_store)
        if prior is not None:
            # Memory only prevents a duplicate WRITE. The agent itself still
            # decided this violation was worth reporting — that decision is
            # never overridden or hidden; it is just told the paperwork
            # already exists instead of being handed a second copy of it.
            # Re-recording (same defect_id, same path) updates last_seen and
            # times_seen so case history reflects genuine recurrence, not
            # just the one original write.
            seen_again = remember_defect(
                prior["rule_id"], prior["story_id"], prior["defect_id"], prior["path"], store=memory_store
            )
            return {
                "defect_id": seen_again["defect_id"],
                "status": "pending_review",
                "path": seen_again["path"],
                "created_at": seen_again["last_seen"],
                "duplicate_of": seen_again["defect_id"],
                "note": (
                    f"A defect for {seen_again['rule_id']}/{seen_again['story_id']} was already "
                    f"on file (first seen {seen_again['first_seen']}, seen "
                    f"{seen_again['times_seen']} time(s) total). No new report was written."
                ),
            }

    try:
        if tool == "check_course_load":
            result = module.run(
                arguments["year_of_study"],
                arguments["units_requested"],
            )
        else:
            writer = None
            if inject == "write_failure":
                def writer(_path, _text):
                    raise DefectWriteError("simulated disk write failure")

            result = module.run(
                arguments["story_id"],
                arguments["rule_id"],
                arguments["title"],
                arguments["description"],
                arguments["severity"],
                defects_dir=defects_dir,
                writer=writer,
            )
    except DefectWriteError as exc:
        return tool_error("unavailable", tool, f"Could not write defect report: {exc}")
    except OSError as exc:
        return tool_error("unavailable", tool, f"Tool dependency failed: {exc}")

    if is_tool_error(result) or not module.output_is_valid(result):
        return tool_error(
            "unexpected_response",
            tool,
            "Tool ran but the result did not match its output schema.",
        )

    if tool == "create_defect_report":
        remember_defect(
            arguments["rule_id"],
            arguments["story_id"],
            result["defect_id"],
            result["path"],
            store=memory_store,
        )

    return result
