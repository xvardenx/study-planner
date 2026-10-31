"""Behavioral checks for the handcrafted Bayesian network."""

from itertools import product

import pytest

from study_planner.inference import build_network, exam_success_probability
from study_planner.inference.engine import days_to_exam_state


def test_network_has_ten_variables_and_normalized_cpds() -> None:
    """Keep the assignment-sized model valid as its parameters evolve."""
    network = build_network()

    assert len(network.nodes()) == 10
    assert network.check_model()
    assert len(network.get_cpds("Readiness").get_values()[0]) == 729
    for cpd in network.get_cpds():
        assert all(sum(column) == pytest.approx(1) for column in zip(*cpd.get_values()))


def test_difficulty_changes_success_with_mastery_held_constant() -> None:
    """Harder concepts must reduce predicted success for the same student."""
    easy = exam_success_probability(("easy",) * 3, ("medium",) * 3, "medium", 5)
    hard = exam_success_probability(("hard",) * 3, ("medium",) * 3, "medium", 5)

    assert easy > hard
    assert easy == pytest.approx(0.498811, abs=1e-6)
    assert hard == pytest.approx(0.286638, abs=1e-6)


def test_mastery_stress_and_time_change_success_in_expected_directions() -> None:
    """Check that the three main decision inputs influence the outcome."""
    difficulties = ("medium",) * 3
    low_mastery = exam_success_probability(difficulties, ("low",) * 3, "medium", 5)
    high_mastery = exam_success_probability(difficulties, ("high",) * 3, "medium", 5)
    low_stress = exam_success_probability(difficulties, ("medium",) * 3, "low", 5)
    high_stress = exam_success_probability(difficulties, ("medium",) * 3, "high", 5)
    distant = exam_success_probability(difficulties, ("medium",) * 3, "medium", 10)
    urgent = exam_success_probability(difficulties, ("medium",) * 3, "medium", 1)

    assert high_mastery > low_mastery
    assert low_stress > high_stress
    assert distant > urgent


def test_cpt_success_is_monotonic_for_all_parent_combinations() -> None:
    """Prevent local CPT exceptions to the documented directional assumptions."""
    cpd = build_network().get_cpds("ExamSuccess")
    for stress, time in product(
        ("low", "medium", "high"), ("urgent", "near", "distant")
    ):
        values = [
            cpd.get_value(
                ExamSuccess="success",
                Readiness=readiness,
                Stress=stress,
                DaysToExam=time,
            )
            for readiness in ("low", "medium", "high")
        ]
        assert values[0] < values[1] < values[2]


@pytest.mark.parametrize(
    ("days", "state"),
    [(1, "urgent"), (2, "urgent"), (3, "near"), (7, "near"), (8, "distant")],
)
def test_days_to_exam_buckets(days: int, state: str) -> None:
    """Preserve the documented inclusive bucket boundaries."""
    assert days_to_exam_state(days) == state


@pytest.mark.parametrize("days", [0, -1])
def test_nonpositive_days_are_rejected(days: int) -> None:
    """Avoid silently treating exam day or malformed days as evidence."""
    with pytest.raises(ValueError):
        days_to_exam_state(days)


@pytest.mark.parametrize("days", [1.5, True])
def test_noninteger_days_are_rejected(days: object) -> None:
    """Ensure fractional and boolean inputs are not treated as dates."""
    with pytest.raises(TypeError):
        days_to_exam_state(days)


def test_incomplete_or_invalid_evidence_is_rejected() -> None:
    """Require all three concept pairs and a known stress category."""
    with pytest.raises(ValueError):
        exam_success_probability(("easy", "hard"), ("low",) * 3, "low", 2)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        exam_success_probability(("easy",) * 3, ("low",) * 3, "extreme", 2)
