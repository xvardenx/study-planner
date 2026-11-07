"""Behavioral checks for daily expected-utility action selection."""

import pytest

from study_planner.inference import exam_success_probability
from study_planner.planning import (
    ActionEvaluation,
    DailyAction,
    DailyDecision,
    evaluate_daily_actions,
)
from study_planner.planning.decision import (
    _mastery_outcomes,
    _select_recommendation,
    _stress_outcomes,
)


def _evaluation(
    decision_action: DailyAction, decision: DailyDecision
) -> ActionEvaluation:
    """Find an action score in a decision report for readable tests."""
    return next(
        evaluation
        for evaluation in decision.evaluations
        if evaluation.action is decision_action
    )


def test_five_actions_and_priority_allocation() -> None:
    """Expose all daily commitments and allocate hours to weaker concepts."""
    decision = evaluate_daily_actions(
        ("hard", "medium", "easy"), ("low", "low", "low"), "low", 5
    )
    assert [item.study_hours for item in decision.evaluations] == [0, 1, 2, 3, 5]
    assert [item.concept_hours for item in decision.evaluations] == [
        (0, 0, 0),
        (1, 0, 0),
        (1, 1, 0),
        (1, 1, 1),
        (2, 2, 1),
    ]


def test_hours_are_reallocated_when_concepts_are_mastered() -> None:
    """Keep the action's full daily hours even when only review is possible."""
    one_eligible = evaluate_daily_actions(
        ("hard", "medium", "easy"), ("high", "low", "high"), "low", 5
    )
    all_mastered = evaluate_daily_actions(
        ("hard", "medium", "easy"), ("high", "high", "high"), "low", 5
    )
    assert _evaluation(DailyAction.INTENSIVE_STUDY, one_eligible).concept_hours == (
        0,
        5,
        0,
    )
    assert _evaluation(DailyAction.INTENSIVE_STUDY, all_mastered).concept_hours == (
        2,
        2,
        1,
    )
    assert all_mastered.recommended.action is DailyAction.REST


def test_mastery_and_stress_outcomes_are_normalized_and_capped() -> None:
    """Check that independent effects form valid distributions at state limits."""
    mastery_outcomes = list(_mastery_outcomes(("high", "low", "medium"), (2, 2, 1)))
    assert sum(probability for _, probability in mastery_outcomes) == pytest.approx(1)
    assert all(states[0] == "high" for states, _ in mastery_outcomes)
    assert _stress_outcomes("low", DailyAction.REST) == (("low", 1.0),)
    assert _stress_outcomes("high", DailyAction.INTENSIVE_STUDY) == (("high", 1.0),)


def test_one_hour_expected_utility_matches_outcome_average() -> None:
    """Average the two possible mastery states before applying utility."""
    difficulties = ("medium", "easy", "easy")
    masteries = ("low", "high", "high")
    decision = evaluate_daily_actions(difficulties, masteries, "low", 5)
    light = _evaluation(DailyAction.LIGHT_REVIEW, decision)
    unchanged = exam_success_probability(difficulties, masteries, "low", 5)
    advanced = exam_success_probability(
        difficulties, ("medium", "high", "high"), "low", 5
    )
    expected_success = 0.55 * unchanged + 0.45 * advanced
    assert light.expected_success_probability == pytest.approx(expected_success)
    assert light.expected_stress_index == 0
    assert light.expected_utility == pytest.approx(100 * expected_success - 0.15)


def test_rest_reduces_expected_stress_and_urgent_study_costs_more() -> None:
    """Value potential stress relief and apply the urgent cramming penalty."""
    evidence = (("medium",) * 3, ("medium",) * 3, "medium")
    near = evaluate_daily_actions(*evidence, 5)
    urgent = evaluate_daily_actions(*evidence, 2)
    assert _evaluation(DailyAction.REST, near).expected_stress_index == pytest.approx(
        0.85
    )
    assert _evaluation(DailyAction.INTENSIVE_STUDY, near).expected_stress_index == (
        pytest.approx(1.25)
    )
    near_five = _evaluation(DailyAction.INTENSIVE_STUDY, near)
    urgent_five = _evaluation(DailyAction.INTENSIVE_STUDY, urgent)
    # The distinct days-to-exam values also change the model's success chance.
    assert urgent_five.expected_utility == pytest.approx(
        100 * urgent_five.expected_success_probability
        - 5 * urgent_five.expected_stress_index
        - 0.15 * 25
        - 0.3 * 5
    )
    assert near_five.expected_utility == pytest.approx(
        100 * near_five.expected_success_probability
        - 5 * near_five.expected_stress_index
        - 0.15 * 25
    )


def test_recommendation_adapts_to_mastery_and_difficulty() -> None:
    """Select rest for mastery and different study loads for concept difficulty."""
    mastered = evaluate_daily_actions(("medium",) * 3, ("high",) * 3, "low", 10)
    easy = evaluate_daily_actions(("easy",) * 3, ("medium", "medium", "high"), "low", 2)
    hard = evaluate_daily_actions(("hard",) * 3, ("medium", "medium", "high"), "low", 2)
    intensive = evaluate_daily_actions(("easy",) * 3, ("low",) * 3, "low", 5)
    assert mastered.recommended.action is DailyAction.REST
    assert easy.recommended.action is DailyAction.STANDARD_STUDY
    assert hard.recommended.action is DailyAction.FOCUSED_STUDY
    assert intensive.recommended.action is DailyAction.INTENSIVE_STUDY


def test_exact_utility_tie_prefers_fewer_hours() -> None:
    """Make the stated tie rule independent of catalog ordering."""
    five = ActionEvaluation(DailyAction.INTENSIVE_STUDY, 5, (2, 2, 1), 0.5, 1, 40)
    one = ActionEvaluation(DailyAction.LIGHT_REVIEW, 1, (1, 0, 0), 0.5, 1, 40)
    assert _select_recommendation((five, one)) is one


@pytest.mark.parametrize(
    ("difficulties", "masteries", "stress", "days"),
    [
        (("easy",), ("low",) * 3, "low", 5),
        (("easy",) * 3, ("low",) * 3, "extreme", 5),
        (("easy",) * 3, ("low",) * 3, "low", 0),
    ],
)
def test_invalid_evidence_uses_inference_validation(
    difficulties: tuple[str, ...],
    masteries: tuple[str, ...],
    stress: str,
    days: int,
) -> None:
    """Reject malformed evidence before scoring any action."""
    with pytest.raises(ValueError):
        evaluate_daily_actions(difficulties, masteries, stress, days)
