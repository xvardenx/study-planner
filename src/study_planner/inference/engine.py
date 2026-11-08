"""Exact inference for complete daily scenario evidence."""

import json
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast

from pgmpy.factors.discrete import DiscreteFactor
from pgmpy.inference import VariableElimination

from study_planner.inference.network import (
    DIFFICULTY_STATES,
    MASTERY_STATES,
    STRESS_STATES,
    build_network,
)

ROOT_PATH = Path(__file__).parents[3]


@dataclass
class Scenario:
    days_to_exam: int
    concept_difficulties: tuple[str, str, str]
    concept_masteries: tuple[str, str, str]
    stress: str

    def __post_init__(self):
        self.exam_state = days_to_exam_state(self.days_to_exam)


def days_to_exam_state(days_remaining: int) -> str:
    """Convert the exact number of days to the BN's exam-proximity state."""
    if isinstance(days_remaining, bool) or not isinstance(days_remaining, int):
        raise TypeError("days_remaining must be an integer")
    if days_remaining < 1:
        raise ValueError("days_remaining must be at least 1")
    if days_remaining <= 2:
        return "urgent"
    if days_remaining <= 7:
        return "near"
    return "distant"


@lru_cache(maxsize=1)
def _inference() -> VariableElimination:
    """Reuse the fixed model across daily inference calls."""
    return VariableElimination(build_network())


def exam_success_probability(
    difficulties: Sequence[str],
    masteries: Sequence[str],
    stress: str,
    days_remaining: int,
) -> float:
    """Query success given complete concept, stress, and exam-date evidence."""
    if len(difficulties) != 3 or any(
        state not in DIFFICULTY_STATES for state in difficulties
    ):
        raise ValueError("difficulties must contain three easy/medium/hard states")
    if len(masteries) != 3 or any(state not in MASTERY_STATES for state in masteries):
        raise ValueError("masteries must contain three low/medium/high states")
    if stress not in STRESS_STATES:
        raise ValueError("stress must be low, medium, or high")

    time_state = days_to_exam_state(days_remaining)
    evidence: dict[Hashable, str] = {"Stress": stress, "DaysToExam": time_state}
    for index, (difficulty, mastery) in enumerate(
        zip(difficulties, masteries, strict=True), 1
    ):
        evidence[f"Difficulty{index}"] = difficulty
        evidence[f"Mastery{index}"] = mastery

    # pgmpy annotates evidence values as integers, but named CPDs require state names.
    pgmpy_evidence = cast(dict[Hashable, int], evidence)
    posterior = cast(
        DiscreteFactor,
        _inference().query(
            ["ExamSuccess"], evidence=pgmpy_evidence, joint=True, show_progress=False
        ),
    )
    return float(posterior.get_value(ExamSuccess="success"))


def load_scenario(scenario_name: str):

    scenario_path = ROOT_PATH / "scenarios"
    scenario = scenario_path / f"{scenario_name}.json"

    with open(scenario, "r") as file:
        scenario_data: dict = json.load(file)

    return Scenario(
        days_to_exam=scenario_data["days_to_exam"],
        concept_difficulties=tuple(scenario_data["concept_difficulties"]),
        concept_masteries=tuple(scenario_data["concept_masteries"]),
        stress=scenario_data["stress"],
    )
