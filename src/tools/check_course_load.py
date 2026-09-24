"""Tool 1 — check_course_load.

Owner: Yohana Mahamat Abdelrassoul (Week 4 tools / orchestration)

Thin adapter around uniflow_core.rules.check_course_load. No new
business logic: the Year 1-4 limits stay in rules.py (R-04).
"""

from __future__ import annotations

from uniflow_core.rules import check_course_load as _check


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_arguments(arguments: dict) -> str | None:
    """Return a missing/invalid field description, or None if the schema holds.

    Year 0/5 is a schema violation (invalid_parameter), not a rule-function
    call. The catalogue wants that distinction kept visible in the traces.
    """
    required = ("year_of_study", "units_requested")
    missing = [name for name in required if name not in arguments]
    if missing:
        return f"missing:{','.join(missing)}"

    year = arguments["year_of_study"]
    units = arguments["units_requested"]
    if not _is_int(year):
        return "invalid:year_of_study must be an integer"
    if year < 1 or year > 4:
        return "invalid:year_of_study must be between 1 and 4"
    if not _is_int(units):
        return "invalid:units_requested must be an integer"
    if units < 0:
        return "invalid:units_requested must be >= 0"
    return None


def run(year_of_study: int, units_requested: int) -> dict:
    """Execute R-04 and return the catalogue output schema."""
    result = _check(year_of_study, units_requested)
    value = None
    # Catalogue: value is null when ok is false — keep the Result shape.
    if result.ok and isinstance(result.value, dict) and "limit" in result.value:
        value = {"limit": result.value["limit"]}
    return {
        "ok": result.ok,
        "rule": result.rule,
        "message": result.message,
        "value": value,
    }


def output_is_valid(obj: object) -> bool:
    if not isinstance(obj, dict):
        return False
    if set(obj) != {"ok", "rule", "message", "value"}:
        return False
    if not isinstance(obj["ok"], bool):
        return False
    if obj["rule"] != "R-04":
        return False
    if not isinstance(obj["message"], str) or not obj["message"]:
        return False
    value = obj["value"]
    if value is None:
        return True
    return isinstance(value, dict) and isinstance(value.get("limit"), int)
