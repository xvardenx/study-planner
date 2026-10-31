"""Ten-variable Bayesian network for three course concepts."""

from itertools import product
from math import exp

from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import DiscreteBayesianNetwork

DIFFICULTY_STATES = ("easy", "medium", "hard")
MASTERY_STATES = ("low", "medium", "high")
READINESS_STATES = ("low", "medium", "high")
STRESS_STATES = ("low", "medium", "high")
TIME_STATES = ("urgent", "near", "distant")
SUCCESS_STATES = ("failure", "success")

CONCEPT_PARENTS = tuple(
    variable
    for index in range(1, 4)
    for variable in (f"Difficulty{index}", f"Mastery{index}")
)


def _readiness_column(states: tuple[str, ...]) -> list[float]:
    """Turn three difficulty and mastery pairs into a readiness distribution."""
    scores = [
        2 * MASTERY_STATES.index(states[index + 1])
        - DIFFICULTY_STATES.index(states[index])
        for index in (0, 2, 4)
    ]
    mean_score = sum(scores) / 3
    centers = (-1.0, 1.0, 3.0)
    weights = [exp(-((mean_score - center) ** 2) / (2 * 1.25**2)) for center in centers]
    total = sum(weights)
    return [weight / total for weight in weights]


def _success_probability(readiness: str, stress: str, time: str) -> float:
    """Calculate the handcrafted success chance for one parent-state column."""
    readiness_effect = 1.1 * (READINESS_STATES.index(readiness) - 1)
    stress_effect = -0.35 * (STRESS_STATES.index(stress) - 1)
    time_effect = {"urgent": -0.5, "near": 0.0, "distant": 0.35}[time]
    log_odds = -0.5 + readiness_effect + stress_effect + time_effect
    return 1 / (1 + exp(-log_odds))


def build_network() -> DiscreteBayesianNetwork:
    """Build and validate the fixed Bayesian network and its handcrafted CPTs."""
    graph = DiscreteBayesianNetwork(
        [(parent, "Readiness") for parent in CONCEPT_PARENTS]
        + [
            ("Readiness", "ExamSuccess"),
            ("Stress", "ExamSuccess"),
            ("DaysToExam", "ExamSuccess"),
        ]
    )

    root_states = {
        **{f"Difficulty{index}": DIFFICULTY_STATES for index in range(1, 4)},
        **{f"Mastery{index}": MASTERY_STATES for index in range(1, 4)},
        "Stress": STRESS_STATES,
        "DaysToExam": TIME_STATES,
    }
    root_cpds = [
        TabularCPD(
            name,
            len(states),
            [[1 / len(states)] for _ in states],
            state_names={name: states},
        )
        for name, states in root_states.items()
    ]

    concept_combinations = list(
        product(*(root_states[parent] for parent in CONCEPT_PARENTS))
    )
    readiness_columns = [_readiness_column(states) for states in concept_combinations]
    readiness_cpd = TabularCPD(
        "Readiness",
        3,
        [list(row) for row in zip(*readiness_columns, strict=True)],
        evidence=list(CONCEPT_PARENTS),
        evidence_card=[3] * 6,
        state_names={
            "Readiness": READINESS_STATES,
            **{parent: root_states[parent] for parent in CONCEPT_PARENTS},
        },
    )

    success_columns = [
        _success_probability(readiness, stress, time)
        for readiness, stress, time in product(
            READINESS_STATES, STRESS_STATES, TIME_STATES
        )
    ]
    success_cpd = TabularCPD(
        "ExamSuccess",
        2,
        [[1 - probability for probability in success_columns], success_columns],
        evidence=["Readiness", "Stress", "DaysToExam"],
        evidence_card=[3, 3, 3],
        state_names={
            "ExamSuccess": SUCCESS_STATES,
            "Readiness": READINESS_STATES,
            "Stress": STRESS_STATES,
            "DaysToExam": TIME_STATES,
        },
    )
    graph.add_cpds(*root_cpds, readiness_cpd, success_cpd)
    graph.check_model()
    return graph
