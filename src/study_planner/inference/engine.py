"""Exact inference for complete daily scenario evidence."""

from functools import lru_cache

from pgmpy.inference import VariableElimination

from study_planner.inference.network import (
    DIFFICULTY_STATES,
    MASTERY_STATES,
    STRESS_STATES,
    build_network,
)


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
    difficulties: tuple[str, str, str],
    masteries: tuple[str, str, str],
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

    evidence = {"Stress": stress, "DaysToExam": days_to_exam_state(days_remaining)}
    for index, (difficulty, mastery) in enumerate(
        zip(difficulties, masteries, strict=True), 1
    ):
        evidence[f"Difficulty{index}"] = difficulty
        evidence[f"Mastery{index}"] = mastery

    posterior = _inference().query(
        ["ExamSuccess"], evidence=evidence, show_progress=False
    )
    return float(posterior.get_value(ExamSuccess="success"))
