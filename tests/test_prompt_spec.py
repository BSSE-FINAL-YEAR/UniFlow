"""Week 7 (Failure F6): the prompt spec must match the running prompt."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import tool_baseline  # noqa: E402

SPEC = (ROOT / "prompts" / "tool_caller_v1.1.md").read_text(encoding="utf-8")


def test_spec_contains_the_running_system_prompt():
    assert tool_baseline.SYSTEM in SPEC


def test_spec_contains_the_running_output_contract():
    assert tool_baseline.OUTPUT_CONTRACT.strip("\n") in SPEC


def test_spec_states_the_running_fingerprint():
    assert f"`{tool_baseline.PROMPT_SHA}`" in SPEC


def test_example_json_reaches_the_model_with_single_braces():
    prompt = tool_baseline._user_prompt("x", [])
    assert "{{" not in prompt and "}}" not in prompt


def test_story_table_in_prompt_matches_validation_table():
    from tools.create_defect_report import RULE_STORIES
    prompt = tool_baseline._user_prompt("x", [])
    for rule, stories in RULE_STORIES.items():
        assert f"{rule}: {' or '.join(stories)}" in prompt
