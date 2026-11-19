"""Validation checks for dated comprehensive scenario observations."""

import json
from copy import deepcopy

import pytest

from study_planner import scenarios
from study_planner.scenarios import SCENARIO_DIR, load_comprehensive_scenario


@pytest.fixture
def replay_data() -> dict:
    """Read the complete example so malformed cases vary one field at a time."""
    return json.loads((SCENARIO_DIR / "comprehensive" / "progressing.json").read_text())


@pytest.fixture
def write_replay(tmp_path, monkeypatch):
    """Write isolated comprehensive inputs under the loader's scenario root."""
    directory = tmp_path / "comprehensive"
    directory.mkdir()
    monkeypatch.setattr(scenarios, "SCENARIO_DIR", tmp_path)

    def write(data):
        """Save the supplied JSON document as the isolated named scenario."""
        (directory / "example.json").write_text(json.dumps(data))
        return "example"

    return write


def test_daily_records_are_sorted_and_use_typed_evidence(replay_data, write_replay):
    """Input order does not determine dates or days remaining."""
    replay_data["days"].reverse()
    result = load_comprehensive_scenario(write_replay(replay_data))
    assert [day.date.day for day in result.days] == list(range(16, 22))
    assert result.days[0].study_window.start.hour == 9
    assert result.days[0].concept_masteries == ("low", "low", "low")


@pytest.mark.parametrize(
    "change, message",
    [
        ("duplicate", "duplicate"),
        ("missing", "missing dates"),
        ("exam_day", "out-of-range"),
        ("masteries", "2026-11-16.*concept_masteries"),
        ("stress", "2026-11-16.*stress"),
        ("window", "2026-11-16.*study_window"),
        ("time", "2026-11-16.*busy_blocks"),
        ("busy_shape", "2026-11-16.*busy_blocks"),
        ("difficulties", "concept_difficulties"),
        ("past_exam", "exam date"),
        ("days_shape", "days"),
    ],
)
def test_invalid_comprehensive_records_are_rejected(
    replay_data, write_replay, change, message
):
    """Reject malformed calendars and evidence with useful field/date context."""
    first = replay_data["days"][0]
    if change == "duplicate":
        replay_data["days"].append(deepcopy(first))
    elif change == "missing":
        replay_data["days"].pop()
    elif change == "exam_day":
        first["date"] = replay_data["exam_date"]
    elif change == "masteries":
        first["concept_masteries"] = ["unknown"] * 3
    elif change == "stress":
        first["stress"] = "extreme"
    elif change == "window":
        first["study_window"]["end"] = "08:00"
    elif change == "time":
        first["busy_blocks"][0]["start"] = "09:00:00"
    elif change == "busy_shape":
        first["busy_blocks"] = {}
    elif change == "difficulties":
        replay_data["concept_difficulties"] = ["easy"]
    elif change == "past_exam":
        replay_data["exam_date"] = replay_data["start_date"]
    elif change == "days_shape":
        replay_data["days"] = {}
    with pytest.raises(ValueError, match=message):
        load_comprehensive_scenario(write_replay(replay_data))


def test_missing_file_is_distinct_from_invalid_json(write_replay, tmp_path):
    """Keep absent scenarios distinguishable from malformed existing files."""
    with pytest.raises(FileNotFoundError):
        load_comprehensive_scenario("absent")
    write_replay({})
    (tmp_path / "comprehensive" / "example.json").write_text("{")
    with pytest.raises(ValueError, match="invalid comprehensive scenario"):
        load_comprehensive_scenario("example")
