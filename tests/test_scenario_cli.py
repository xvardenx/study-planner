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
    assert struggling.recommended.action is DailyAction.EXTENDED_STUDY
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
    assert "extended study" in output
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


def test_cli_comprehensive_displays_each_date_and_assigned_sessions():
    """Replay all days and expose capacity, decisions, and concrete session times."""
    result = runner.invoke(app, ["run-comp", "progressing"])
    assert result.exit_code == 0, result.output
    for day in range(16, 22):
        assert f"2026-11-{day}" in result.stdout
    assert "2026-11-22" not in result.stdout
    assert result.stdout.count("Baseline success:") == 6
    assert result.stdout.count("Available study capacity:") == 6
    assert result.stdout.count("Scheduled hours:") == 6
    assert "Assigned study sessions" in result.stdout
    assert "09:00:00" in result.stdout


def test_cli_comprehensive_distinguishes_missing_and_malformed(monkeypatch, tmp_path):
    """Invalid existing data must not be misreported as an unknown name."""
    from study_planner import scenarios

    directory = tmp_path / "comprehensive"
    directory.mkdir()
    monkeypatch.setattr(scenarios, "SCENARIO_DIR", tmp_path)
    missing = runner.invoke(app, ["run-comp", "absent"])
    assert missing.exit_code != 0
    assert "Unknown comprehensive scenario" in missing.output
    (directory / "broken.json").write_text("{}")
    broken = runner.invoke(app, ["run-comp", "broken"])
    assert broken.exit_code != 0
    assert "invalid comprehensive scenario" in broken.output
    assert "Unknown comprehensive scenario" not in broken.output


def test_cli_comprehensive_reports_rest_day(monkeypatch):
    """Explain empty session output when a day's calendar is fully occupied."""
    from dataclasses import replace

    from study_planner import cli
    from study_planner.scenarios import load_comprehensive_scenario

    scenario = load_comprehensive_scenario("progressing")
    first = scenario.days[0]
    scenario = replace(
        scenario,
        days=(replace(first, busy_blocks=(first.study_window,)), *scenario.days[1:]),
    )
    monkeypatch.setattr(cli, "load_comprehensive_scenario", lambda name: scenario)
    result = runner.invoke(app, ["run-comp", "progressing"])
    assert result.exit_code == 0, result.output
    assert "No study sessions assigned." in result.stdout
    assert "Available study capacity: 0 hours" in result.stdout
