"""Integration checks for example scenario loading and CLI reporting."""

import subprocess
import sys

from typer.testing import CliRunner

from study_planner.cli import app
from study_planner.planning import DailyAction
from study_planner.scenarios import (
    SCENARIO_DIR,
    evaluate_scenario,
    load_scenario,
)

runner = CliRunner()


def test_example_scenarios_change_the_recommendation() -> None:
    """Check that the JSON examples drive distinct decisions through the model."""
    advanced = evaluate_scenario(load_scenario(SCENARIO_DIR / "advanced.json"))
    struggling = evaluate_scenario(load_scenario(SCENARIO_DIR / "struggling.json"))

    assert advanced.recommended.action is DailyAction.REST
    assert struggling.recommended.action is DailyAction.INTENSIVE_STUDY
    assert (
        advanced.baseline_success_probability > struggling.baseline_success_probability
    )


def test_cli_reports_every_scenario() -> None:
    """Show baseline inference, action scores, and recommendations for each file."""
    result = runner.invoke(app, ["all"])
    assert result.exit_code == 0
    output = result.stdout
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        assert path.stem in output
    assert output.count("Baseline success:") == len(list(SCENARIO_DIR.glob("*.json")))
    assert output.count("Recommended:") == len(list(SCENARIO_DIR.glob("*.json")))
    assert "intensive study" in output
    assert "rest" in output


def test_cli_runs_one_scenario() -> None:
    """Display only the requested scenario and its full action comparison."""
    result = runner.invoke(app, ["run", "mixed"])
    assert result.exit_code == 0
    assert "mixed" in result.stdout
    assert "advanced" not in result.stdout
    assert "Baseline success:" in result.stdout
    assert "focused study" in result.stdout
    assert "Recommended:" in result.stdout


def test_cli_rejects_unknown_scenario() -> None:
    """Explain invalid names and list the available built-in scenarios."""
    result = runner.invoke(app, ["run", "unknown"])
    assert result.exit_code != 0
    assert "Unknown scenario 'unknown'" in result.output
    assert "advanced, mixed, stressed, struggling" in result.output


def test_cli_startup_omits_pgmpy_deprecation_warning() -> None:
    """Keep pgmpy's unrelated estimator deprecation out of CLI output."""
    result = subprocess.run(
        [sys.executable, "-m", "study_planner.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "`pgmpy.estimators.StructureScore` is deprecated" not in result.stderr
