"""Validate-then-call dispatcher for the Week 4 allow-list.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

Never guesses a missing value. Never calls a tool that is not listed.
Output is either the tool's success/domain schema or the shared error envelope.
"""

from __future__ import annotations

from pathlib import Path

from .create_defect_report import DefectWriteError
from .errors import is_tool_error, tool_error
from .registry import ALLOW_LIST, is_allowed


def dispatch(
    tool: str,
    arguments: dict | None,
    *,
    inject: str | None = None,
    defects_dir: Path | None = None,
) -> dict:
    """Run one approved tool. `inject` is only for designed failure tests."""
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
    return result
