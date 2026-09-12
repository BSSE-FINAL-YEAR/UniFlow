"""
UniFlow core — business rules as pure functions.

Owner: Odongo Emmanuel (Backend / System Lead)

This is NOT the full UniFlow system and is not a Week 2 deliverable. It is the
minimum deterministic surface the QA Agent will actually run tests against in
Week 4, built now so Weeks 3-4 are not blocked.

Deliberately: no database, no framework, no I/O. Pure functions over plain data,
each one mapping to a numbered rule in prompts/context/uniflow_rules.md.
That mapping is what lets a generated test case be executed automatically later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import time
from typing import cast

REG_NO_PATTERN = re.compile(r"^(\d{2})/([A-Z])/(\d{5})/(PS|EVE)$")

# R-04
MAX_COURSE_LOAD = {1: 6, 2: 6, 3: 5, 4: 4}

# R-05
DAY_WINDOW = (time(8, 0), time(16, 0))
EVENING_WINDOW = (time(16, 30), time(20, 30))

# R-06
MIN_SESSIONS_PER_WEEK = 1
MAX_SESSIONS_PER_WEEK = 2


@dataclass(frozen=True)
class Result:
    ok: bool
    rule: str
    message: str
    value: object = None

    def __bool__(self) -> bool:
        return self.ok


def parse_registration_number(reg_no: str) -> Result:
    """R-01: validate format and derive the student number.

    23/U/05288/PS -> 2305288.  The PS/EVE suffix is NOT part of the identity.
    """
    match = REG_NO_PATTERN.match((reg_no or "").strip().upper())
    if not match:
        return Result(False, "R-01", f"Invalid registration number format: {reg_no!r}")
    year, _college, serial, mode = match.groups()
    return Result(True, "R-01", "Valid registration number",
                  {"student_number": f"{year}{serial}", "study_mode": mode})


def check_duplicate_student_number(reg_no: str, existing_reg_nos: list[str]) -> Result:
    """R-01: reject a second record with an existing derived student number.

    The suffix does not disambiguate: 23/U/05288/PS and 23/U/05288/EVE collide.
    """
    parsed = parse_registration_number(reg_no)
    if not parsed:
        return parsed

    parsed_value = cast(dict[str, str], parsed.value)
    new_number = parsed_value["student_number"]
    for existing in existing_reg_nos:
        prior = parse_registration_number(existing)
        if prior:
            prior_value = cast(dict[str, str], prior.value)
            if prior_value.get("student_number") == new_number:
                return Result(False, "R-01",
                              f"Student number {new_number} already exists (from {existing}). "
                              f"The PS/EVE suffix does not create a distinct student.")
    return Result(True, "R-01", f"Student number {new_number} is unique")


def check_course_load(year_of_study: int, units_requested: int) -> Result:
    """R-04: Y1:6, Y2:6, Y3:5, Y4:4."""
    if year_of_study not in MAX_COURSE_LOAD:
        return Result(False, "R-04", f"Unsupported year of study: {year_of_study}")
    limit = MAX_COURSE_LOAD[year_of_study]
    if units_requested > limit:
        return Result(False, "R-04",
                      f"Course load {units_requested} exceeds Year {year_of_study} maximum of {limit}")
    return Result(True, "R-04", f"Course load {units_requested} within Year {year_of_study} limit of {limit}",
                  {"limit": limit})


def check_teaching_window(study_mode: str, start: time, end: time) -> Result:
    """R-05: PS 08:00-16:00, EVE 16:30-20:30."""
    mode = (study_mode or "").upper()
    if mode not in {"PS", "EVE"}:
        return Result(False, "R-05", f"Unknown study mode: {study_mode!r}")
    if end <= start:
        return Result(False, "R-05", "Session end must be after session start")

    window = DAY_WINDOW if mode == "PS" else EVENING_WINDOW
    lo, hi = window
    if start < lo or end > hi:
        label = "Day" if mode == "PS" else "Evening"
        return Result(False, "R-05",
                      f"{label} session {start:%H:%M}-{end:%H:%M} falls outside "
                      f"the permitted window {lo:%H:%M}-{hi:%H:%M}")
    return Result(True, "R-05", f"Session within the {mode} teaching window")


def check_course_frequency(sessions_per_week: int) -> Result:
    """R-06: at least once, at most twice per week."""
    if sessions_per_week < MIN_SESSIONS_PER_WEEK:
        return Result(False, "R-06", "Course must be taught at least once per week")
    if sessions_per_week > MAX_SESSIONS_PER_WEEK:
        return Result(False, "R-06",
                      f"Course taught {sessions_per_week} times per week exceeds the maximum of 2")
    return Result(True, "R-06", f"Frequency {sessions_per_week}/week is permitted")


def check_duplicate_course_registration(course_code: str, already_registered: list[str]) -> Result:
    """R-07: a course may be registered only once per applicable period."""
    if course_code in already_registered:
        return Result(False, "R-07", f"{course_code} is already registered for this period")
    return Result(True, "R-07", f"{course_code} is not yet registered")


def check_prerequisites(course_code: str, completed: list[str], prereq_map: dict[str, list[str]]) -> Result:
    """R-07: prerequisite satisfaction.

    NOTE: the Week 1 rule pack asserts that prerequisites are checked but does not
    define a concrete prerequisite chain. prereq_map is therefore supplied by the
    caller from synthetic data, not hard-coded here. This gap is deliberate and is
    what evaluation case PE-10 probes.
    """
    required = prereq_map.get(course_code, [])
    missing = [p for p in required if p not in completed]
    if missing:
        return Result(False, "R-07", f"Missing prerequisite(s) for {course_code}: {', '.join(missing)}",
                      {"missing": missing})
    return Result(True, "R-07", f"All prerequisites satisfied for {course_code}")


def detect_timetable_conflicts(sessions: list[dict]) -> Result:
    """R-07/US-10: student, lecturer and room conflicts.

    session = {"course", "day", "start": time, "end": time, "room", "lecturer", "group"}
    """
    conflicts = []
    for i, a in enumerate(sessions):
        for b in sessions[i + 1:]:
            if a["day"] != b["day"]:
                continue
            if a["end"] <= b["start"] or b["end"] <= a["start"]:
                continue
            for key, label in (("room", "Room"), ("lecturer", "Lecturer"), ("group", "Student group")):
                if a.get(key) and a.get(key) == b.get(key):
                    conflicts.append(
                        f"{label} {a[key]} double-booked on {a['day']}: "
                        f"{a['course']} vs {b['course']}"
                    )

    if conflicts:
        return Result(False, "R-07", f"{len(conflicts)} timetable conflict(s) detected", conflicts)
    return Result(True, "R-07", "No timetable conflicts detected")
