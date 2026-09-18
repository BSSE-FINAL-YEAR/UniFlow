"""Unit tests for the deterministic UniFlow rule core. Run: python -m pytest tests/ -q"""
import sys
from datetime import time
from pathlib import Path
from typing import cast

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from uniflow_core.rules import (  # pyright: ignore[reportMissingImports]
    parse_registration_number, check_duplicate_student_number, check_course_load,
    check_teaching_window, check_course_frequency, check_prerequisites,
    detect_timetable_conflicts,
)


def test_r01_derives_student_number():
    r = parse_registration_number("23/U/05288/PS")
    assert r.ok and isinstance(r.value, dict) and cast(dict, r.value)["student_number"] == "2305288"


def test_r01_ps_and_eve_collide():
    assert not check_duplicate_student_number("23/U/05288/EVE", ["23/U/05288/PS"])


def test_r01_rejects_bad_format():
    assert not parse_registration_number("23-U-05288-PS")


def test_r04_year_limits():
    for year, limit in {1: 6, 2: 6, 3: 5, 4: 4}.items():
        assert check_course_load(year, limit).ok
        assert not check_course_load(year, limit + 1).ok


def test_r05_window_boundaries():
    assert check_teaching_window("PS", time(8, 0), time(16, 0)).ok
    assert check_teaching_window("EVE", time(16, 30), time(20, 30)).ok
    assert not check_teaching_window("PS", time(16, 10), time(17, 0)).ok   # the 16:00-16:30 gap
    assert not check_teaching_window("EVE", time(20, 0), time(21, 0)).ok


def test_r06_frequency():
    assert not check_course_frequency(0).ok
    assert check_course_frequency(1).ok and check_course_frequency(2).ok
    assert not check_course_frequency(3).ok


def test_r07_prerequisites():
    m = {"CS201": ["CS101"]}
    assert check_prerequisites("CS201", ["CS101"], m).ok
    assert not check_prerequisites("CS201", [], m).ok


def test_timetable_room_conflict():
    s = [
        {"course": "CS101", "day": "Mon", "start": time(9, 0), "end": time(11, 0), "room": "LLT1", "lecturer": "L1", "group": "G1"},
        {"course": "CS102", "day": "Mon", "start": time(10, 0), "end": time(12, 0), "room": "LLT1", "lecturer": "L2", "group": "G2"},
    ]
    assert not detect_timetable_conflicts(s).ok
