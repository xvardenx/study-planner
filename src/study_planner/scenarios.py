"""Load example evidence and evaluate one-day study decisions."""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from study_planner.calendar.schedule import days_until_exam
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


def load_comprehensive_scenario(name: str) -> list[Scenario]:
    """Loads a comprehensive scenario as a list of individual scenarios."""
    path = SCENARIO_DIR / "comprehensive" / f"{name}.json"
    if not path.exists():
        raise ValueError(f"{path} does not exist")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} expected a JSON object")

    days_to_exam = days_until_exam(
        exam_date=date.fromisoformat(data["exam_date"]),
        start_date=date.fromisoformat(data["start_date"]),
    )
    concept_difficulties = data["concept_difficulties"]
    daily_scenarios = data["days"]
    scenarios: list[Scenario] = []

    for daily_data in daily_scenarios.values():
        scenarios.append(
            Scenario(
                days_to_exam=days_to_exam,
                concept_difficulties=concept_difficulties,
                concept_masteries=daily_data["concept_masteries"],
                stress=daily_data["stress"],
            )
        )
        days_to_exam -= 1

    return scenarios


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
