"""Print inference and daily decisions for the repository's example scenarios."""

from pathlib import Path

from study_planner.scenarios import evaluate_scenario, load_scenario

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "scenarios"


def main() -> None:
    """Evaluate every example JSON file in sorted order and print its results."""
    paths = sorted(SCENARIO_DIR.glob("*.json"))
    if not paths:
        raise SystemExit(f"No scenario JSON files found in {SCENARIO_DIR}")

    for path in paths:
        scenario = load_scenario(path)
        decision = evaluate_scenario(scenario)
        print(f"\n{path.stem}")
        print(f"  Days to exam: {scenario.days_to_exam}; stress: {scenario.stress}")
        print(f"  Difficulties: {', '.join(scenario.concept_difficulties)}")
        print(f"  Masteries:    {', '.join(scenario.concept_masteries)}")
        print(f"  Baseline exam success: {decision.baseline_success_probability:.1%}")
        print(
            "  Action             Hours  Concept hours  Expected success  Stress  Utility"
        )
        for evaluation in decision.evaluations:
            print(
                f"  {evaluation.action.value:18} "
                f"{evaluation.study_hours:>2}     "
                f"{evaluation.concept_hours!s:13}  "
                f"{evaluation.expected_success_probability:>7.1%}       "
                f"{evaluation.expected_stress_index:>4.2f}    "
                f"{evaluation.expected_utility:>6.2f}"
            )
        limit = decision.max_allowed_study_hours
        if limit is not None and any(
            evaluation.study_hours > limit for evaluation in decision.evaluations
        ):
            print(f"  Stress-aware study limit: {limit} hours")
        print(f"  Recommended: {decision.recommended.action.value}")


if __name__ == "__main__":
    main()
