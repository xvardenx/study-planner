"""Expected-utility decisions for one day's study commitment."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import product
from math import prod

from study_planner.inference.engine import (
    days_to_exam_state,
    exam_success_probability,
)
from study_planner.inference.network import (
    DIFFICULTY_STATES,
    MASTERY_STATES,
    STRESS_STATES,
)


class DailyAction(StrEnum):
    """Available total study commitments for one day."""

    REST = "rest"
    LIGHT_REVIEW = "light_review"
    STANDARD_STUDY = "standard_study"
    FOCUSED_STUDY = "focused_study"
    INTENSIVE_STUDY = "intensive_study"


@dataclass(frozen=True)
class ActionEvaluation:
    """One action's allocation and predicted decision outcomes."""

    action: DailyAction
    study_hours: int
    concept_hours: tuple[int, int, int]
    expected_success_probability: float
    expected_stress_index: float
    expected_utility: float


@dataclass(frozen=True)
class DailyDecision:
    """All action scores and the best recommendation within the stress limit."""

    baseline_success_probability: float
    evaluations: tuple[ActionEvaluation, ...]
    recommended: ActionEvaluation
    max_allowed_study_hours: int | None = None


_ACTION_HOURS = {
    DailyAction.REST: 0,
    DailyAction.LIGHT_REVIEW: 1,
    DailyAction.STANDARD_STUDY: 2,
    DailyAction.FOCUSED_STUDY: 3,
    DailyAction.INTENSIVE_STUDY: 5,
}

# Probability of advancing one mastery level after this many hours on a concept.
_MASTERY_GAIN_PROBABILITY = (0.0, 0.45, 0.75, 0.85, 0.92, 0.96)

# Rest reduces stress; study actions can increase it. Changes are one level.
_STRESS_CHANGE_PROBABILITY = {
    DailyAction.REST: 0.15,
    DailyAction.LIGHT_REVIEW: 0.0,
    DailyAction.STANDARD_STUDY: 0.05,
    DailyAction.FOCUSED_STUDY: 0.10,
    DailyAction.INTENSIVE_STUDY: 0.25,
}


def _allocate_hours(
    difficulties: tuple[str, ...], masteries: tuple[str, ...], hours: int
) -> tuple[int, int, int]:
    """Spread hours across improvable concepts by mastery and difficulty.

    Concepts below high mastery are ordered from lowest mastery to highest,
    breaking ties by harder difficulty and then concept number. One hour goes
    to each concept in turn before another round. If all are already high,
    hours become review time allocated by difficulty.
    """
    candidates = [index for index, state in enumerate(masteries) if state != "high"]
    if not candidates:
        candidates = list(range(3))
    candidates.sort(
        key=lambda index: (
            MASTERY_STATES.index(masteries[index]),
            -DIFFICULTY_STATES.index(difficulties[index]),
            index,
        )
    )
    allocation = [0, 0, 0]
    for hour in range(hours):
        allocation[candidates[hour % len(candidates)]] += 1
    return allocation[0], allocation[1], allocation[2]


def _mastery_outcomes(
    masteries: tuple[str, ...], concept_hours: tuple[int, int, int]
) -> Iterator[tuple[tuple[str, ...], float]]:
    """Enumerate independent, at-most-one-level mastery gains for an action."""
    options: list[tuple[tuple[str, float], ...]] = []
    for mastery, hours in zip(masteries, concept_hours, strict=True):
        if mastery == "high" or hours == 0:
            options.append(((mastery, 1.0),))
            continue
        gain_probability = _MASTERY_GAIN_PROBABILITY[hours]
        next_mastery = MASTERY_STATES[MASTERY_STATES.index(mastery) + 1]
        options.append(
            (
                (mastery, 1 - gain_probability),
                (next_mastery, gain_probability),
            )
        )
    for outcome in product(*options):
        yield (
            tuple(state for state, _ in outcome),
            prod(probability for _, probability in outcome),
        )


def _stress_outcomes(stress: str, action: DailyAction) -> tuple[tuple[str, float], ...]:
    """Return unchanged and one-level-changed stress outcomes for an action."""
    current_index = STRESS_STATES.index(stress)
    change_probability = _STRESS_CHANGE_PROBABILITY[action]
    next_index = (
        max(0, current_index - 1)
        if action is DailyAction.REST
        else min(2, current_index + 1)
    )
    if change_probability == 0 or next_index == current_index:
        return ((stress, 1.0),)
    return (
        (stress, 1 - change_probability),
        (STRESS_STATES[next_index], change_probability),
    )


def _evaluate_action(
    action: DailyAction,
    difficulties: tuple[str, ...],
    masteries: tuple[str, ...],
    stress: str,
    days_remaining: int,
    urgent: bool,
) -> ActionEvaluation:
    """Average success and utility across all possible post-action states."""
    hours = _ACTION_HOURS[action]
    concept_hours = _allocate_hours(difficulties, masteries, hours)
    stress_outcomes = _stress_outcomes(stress, action)
    expected_success = 0.0
    expected_stress = sum(
        STRESS_STATES.index(state) * probability
        for state, probability in stress_outcomes
    )
    for next_masteries, mastery_probability in _mastery_outcomes(
        masteries, concept_hours
    ):
        for next_stress, stress_probability in stress_outcomes:
            success = exam_success_probability(
                difficulties, next_masteries, next_stress, days_remaining
            )
            expected_success += mastery_probability * stress_probability * success
    utility = (
        100 * expected_success
        - 5 * expected_stress
        - 0.15 * hours**2
        - 0.03 * STRESS_STATES.index(stress) * hours**2
        - (0.3 * hours if urgent else 0)
    )
    return ActionEvaluation(
        action=action,
        study_hours=hours,
        concept_hours=concept_hours,
        expected_success_probability=expected_success,
        expected_stress_index=expected_stress,
        expected_utility=utility,
    )


def _select_recommendation(
    evaluations: tuple[ActionEvaluation, ...],
    max_study_hours: int | None = None,
) -> ActionEvaluation:
    """Choose the best permitted action, preferring fewer hours for exact ties."""
    return max(
        (
            evaluation
            for evaluation in evaluations
            if max_study_hours is None or evaluation.study_hours <= max_study_hours
        ),
        key=lambda evaluation: (
            evaluation.expected_utility,
            -evaluation.study_hours,
        ),
    )


def evaluate_daily_actions(
    difficulties: Sequence[str],
    masteries: Sequence[str],
    stress: str,
    days_remaining: int,
) -> DailyDecision:
    """Score actions and keep recommended hours nonincreasing with stress.

    The existing inference API validates the evidence. Study and rest effects
    here are handcrafted one-day assumptions; the Bayesian network does not
    learn them or represent a causal intervention.
    """
    baseline = exam_success_probability(difficulties, masteries, stress, days_remaining)
    difficulty_states = tuple(difficulties)
    mastery_states = tuple(masteries)
    urgent = days_to_exam_state(days_remaining) == "urgent"
    max_allowed_study_hours = None
    for stress_level in STRESS_STATES[: STRESS_STATES.index(stress) + 1]:
        evaluations = tuple(
            _evaluate_action(
                action,
                difficulty_states,
                mastery_states,
                stress_level,
                days_remaining,
                urgent,
            )
            for action in DailyAction
        )
        recommended = _select_recommendation(evaluations, max_allowed_study_hours)
        if stress_level == stress:
            return DailyDecision(
                baseline_success_probability=baseline,
                evaluations=evaluations,
                recommended=recommended,
                max_allowed_study_hours=max_allowed_study_hours,
            )
        max_allowed_study_hours = recommended.study_hours
    raise AssertionError("validated stress level was not evaluated")
