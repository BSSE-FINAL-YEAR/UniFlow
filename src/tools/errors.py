"""Shared tool-error envelope from docs/Week4_Tool_Catalogue.md.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

The orchestration layer returns this instead of calling business logic
whenever a call is malformed, unauthorized, or the tool itself failed.
"""

from __future__ import annotations

ERROR_KINDS = (
    "missing_parameter",
    "invalid_parameter",
    "unauthorized",
    "unavailable",
    "unexpected_response",
)


def tool_error(kind: str, tool: str, message: str) -> dict:
    if kind not in ERROR_KINDS:
        raise ValueError(f"unknown tool_error kind: {kind!r}")
    return {"tool_error": kind, "tool": tool, "message": message}


def is_tool_error(obj: object) -> bool:
    return isinstance(obj, dict) and "tool_error" in obj
