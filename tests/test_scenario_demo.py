"""Integration checks for example scenario loading and reporting."""

from study_planner.demo import SCENARIO_DIR, main
from study_planner.planning import DailyAction
from study_planner.scenarios import evaluate_scenario, load_scenario


def test_example_scenarios_change_the_recommendation() -> None:
    """Check that the JSON examples drive distinct decisions through the model."""
    advanced = evaluate_scenario(load_scenario(SCENARIO_DIR / "advanced.json"))
    struggling = evaluate_scenario(load_scenario(SCENARIO_DIR / "struggling.json"))

    assert advanced.recommended.action is DailyAction.REST
    assert struggling.recommended.action is DailyAction.INTENSIVE_STUDY
    assert (
        advanced.baseline_success_probability > struggling.baseline_success_probability
    )


def test_demo_reports_every_scenario(capsys) -> None:
    """Show baseline inference, action scores, and recommendations for each file."""
    main()
    output = capsys.readouterr().out
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        assert f"\n{path.stem}\n" in output
    assert output.count("Baseline exam success:") == len(
        list(SCENARIO_DIR.glob("*.json"))
    )
    assert output.count("Recommended:") == len(list(SCENARIO_DIR.glob("*.json")))
    assert "intensive_study" in output
    assert "rest" in output
