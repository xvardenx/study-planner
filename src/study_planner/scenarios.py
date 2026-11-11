"""Load example evidence and evaluate one-day study decisions."""

import json
from dataclasses import dataclass
from pathlib import Path

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
