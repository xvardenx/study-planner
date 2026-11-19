"""Load and validate single-day evidence and dated comprehensive replays."""

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

from study_planner.calendar.schedule import TimeBlock, days_until_exam
from study_planner.inference.network import (
    DIFFICULTY_STATES,
    MASTERY_STATES,
    STRESS_STATES,
)
from study_planner.planning import DailyDecision, evaluate_daily_actions

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "scenarios"


@dataclass(frozen=True)
class Scenario:
    """Evidence for three concepts and one upcoming exam."""

    days_to_exam: int
    concept_difficulties: tuple[str, str, str]
    concept_masteries: tuple[str, str, str]
    stress: str


def load_scenario(path: Path) -> Scenario:
    """Read scenario evidence from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path}: expected a JSON object")
    try:
        return Scenario(
            days_to_exam=data["days_to_exam"],
            concept_difficulties=tuple(data["concept_difficulties"]),
            concept_masteries=tuple(data["concept_masteries"]),
            stress=data["stress"],
        )
    except (KeyError, TypeError) as error:
        raise ValueError(f"{path}: invalid scenario fields: {error}") from error


def _validate_states(value: object, allowed: tuple[str, ...], field: str) -> None:
    """Validate three concept labels without running inference."""
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 3
        or any(state not in allowed for state in value)
    ):
        raise ValueError(f"{field}: expected three labels from {allowed}")


@dataclass(frozen=True)
class ScenarioDay:
    """Observed evidence and a local calendar snapshot for one study day."""

    date: date
    concept_masteries: tuple[str, str, str]
    stress: str
    study_window: TimeBlock
    busy_blocks: tuple[TimeBlock, ...]

    def __post_init__(self) -> None:
        """Reject invalid observations or calendar intervals outside this date."""
        _validate_states(self.concept_masteries, MASTERY_STATES, "concept_masteries")
        if self.stress not in STRESS_STATES:
            raise ValueError("stress: expected low, medium, or high")
        for block in (self.study_window, *self.busy_blocks):
            if any(
                stamp.date() != self.date or stamp.tzinfo is not None
                for stamp in (block.start, block.end)
            ):
                raise ValueError(
                    "calendar intervals must use this date and local times"
                )


@dataclass(frozen=True)
class ComprehensiveScenario:
    """Validated daily observations covering every day before one exam."""

    start_date: date
    exam_date: date
    concept_difficulties: tuple[str, str, str]
    days: tuple[ScenarioDay, ...]

    def __post_init__(self) -> None:
        """Validate coverage and store observations in chronological order."""
        count = days_until_exam(self.exam_date, self.start_date)
        _validate_states(
            self.concept_difficulties, DIFFICULTY_STATES, "concept_difficulties"
        )
        dates = [day.date for day in self.days]
        if len(dates) != len(set(dates)):
            raise ValueError(
                f"days: duplicate dates {sorted(day for day in set(dates) if dates.count(day) > 1)}"
            )
        expected = {self.start_date + timedelta(days=index) for index in range(count)}
        missing = sorted(expected - set(dates))
        extra = sorted(set(dates) - expected)
        if missing or extra:
            raise ValueError(
                f"days: missing dates {missing}; out-of-range dates {extra}"
            )
        object.__setattr__(
            self, "days", tuple(sorted(self.days, key=lambda day: day.date))
        )


def _parse_date(value: str, field: str = "date") -> date:
    """Read only the documented ISO calendar-date format."""
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError("expected YYYY-MM-DD")
        return parsed
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field}: expected YYYY-MM-DD") from error


def _parse_block(data: dict, day: date, field: str) -> TimeBlock:
    """Read a same-day interval with strict HH:MM endpoints."""
    try:
        endpoints = []
        for key in ("start", "end"):
            value = data[key]
            if not isinstance(value, str) or not re.fullmatch(
                r"[0-9]{2}:[0-9]{2}", value
            ):
                raise ValueError(f"{key}: expected HH:MM")
            endpoints.append(datetime.combine(day, time.fromisoformat(value)))
        return TimeBlock(*endpoints)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{field}: {error}") from error


def load_comprehensive_scenario(name: str) -> ComprehensiveScenario:
    """Load and validate a named daily replay before any inference is run."""
    if Path(name).name != name:
        raise ValueError("scenario name must be a filename stem")
    path = SCENARIO_DIR / "comprehensive" / f"{name}.json"
    # Keep a missing file distinct from invalid JSON or invalid scenario fields.
    raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise TypeError("expected a JSON object")
        start_date = _parse_date(data["start_date"], "start_date")
        exam_date = _parse_date(data["exam_date"], "exam_date")
        difficulties = data["concept_difficulties"]
        _validate_states(difficulties, DIFFICULTY_STATES, "concept_difficulties")
        if not isinstance(data["days"], list):
            raise TypeError("days: expected a list of dated records")
        days = []
        for index, record in enumerate(data["days"], 1):
            context = f"days[{index}]"
            try:
                day = _parse_date(record["date"])
                context = day.isoformat()
                masteries = record["concept_masteries"]
                _validate_states(masteries, MASTERY_STATES, "concept_masteries")
                if not isinstance(record["busy_blocks"], list):
                    raise TypeError("busy_blocks: expected a list")
                days.append(
                    ScenarioDay(
                        date=day,
                        concept_masteries=tuple(masteries),
                        stress=record["stress"],
                        study_window=_parse_block(
                            record["study_window"], day, "study_window"
                        ),
                        busy_blocks=tuple(
                            _parse_block(block, day, f"busy_blocks[{block_index}]")
                            for block_index, block in enumerate(record["busy_blocks"])
                        ),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{context}: {error}") from error
        return ComprehensiveScenario(
            start_date, exam_date, tuple(difficulties), tuple(days)
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path}: invalid comprehensive scenario: {error}") from error


def load_all_scenarios() -> dict[str, Scenario]:
    """Loads all scenarios."""
    paths = sorted(SCENARIO_DIR.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"No scenario JSON files found in {SCENARIO_DIR}")

    scenarios: dict[str, Scenario] = {}

    for path in paths:
        scenarios[path.stem] = load_scenario(path)

    return scenarios


def evaluate_scenario(scenario: Scenario) -> DailyDecision:
    """Return the baseline inference and all action evaluations."""
    return evaluate_daily_actions(
        scenario.concept_difficulties,
        scenario.concept_masteries,
        scenario.stress,
        scenario.days_to_exam,
    )
