"""Command-line access to the repository's example study scenarios."""

import typer
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from study_planner.scenarios import Scenario, evaluate_scenario, load_all_scenarios

app = typer.Typer(help="Evaluate example study-planning scenarios.")


def _show_scenario(console: Console, name: str, scenario: Scenario) -> None:
    """Display the evidence, action comparison, and recommendation for a scenario."""
    decision = evaluate_scenario(scenario)
    console.print(Rule(name, style="cyan"))
    console.print(
        f"Exam in {scenario.days_to_exam} days  •  Stress: {scenario.stress}  •  "
        f"Baseline success: {decision.baseline_success_probability:.1%}"
    )
    console.print(f"Difficulties: {', '.join(scenario.concept_difficulties)}")
    console.print(f"Masteries:    {', '.join(scenario.concept_masteries)}")

    table = Table(show_lines=False, header_style="bold")
    table.add_column("Action")
    table.add_column("Hours", justify="right")
    table.add_column("Concept hours (1/2/3)", justify="right")
    table.add_column("Success", justify="right")
    table.add_column("Stress (0–2)", justify="right")
    table.add_column("Utility", justify="right")
    for evaluation in decision.evaluations:
        table.add_row(
            evaluation.action.value.replace("_", " "),
            str(evaluation.study_hours),
            " / ".join(map(str, evaluation.concept_hours)),
            f"{evaluation.expected_success_probability:.1%}",
            f"{evaluation.expected_stress_index:.2f}",
            f"{evaluation.expected_utility:.2f}",
            style="bold green" if evaluation == decision.recommended else None,
        )
    console.print(table)
    limit = decision.max_allowed_study_hours
    if limit is not None and any(
        evaluation.study_hours > limit for evaluation in decision.evaluations
    ):
        console.print(f"Stress-aware study limit: {limit} hours")
    console.print(
        f"[bold green]Recommended:[/bold green] "
        f"{decision.recommended.action.value.replace('_', ' ')}"
    )


@app.command(name="all")
def run_all_scenarios() -> None:
    """Evaluate and display every built-in scenario."""
    scenarios = load_all_scenarios()
    console = Console()
    for name, scenario in scenarios.items():
        _show_scenario(console, name, scenario)


@app.command()
def run(name: str) -> None:
    """Evaluate a built-in scenario by name (for example, mixed)."""
    scenarios = load_all_scenarios()
    if name not in scenarios:
        available = ", ".join(scenarios)
        raise typer.BadParameter(
            f"Unknown scenario '{name}'. Available scenarios: {available}",
            param_hint="NAME",
        )
    _show_scenario(Console(), name, scenarios[name])


if __name__ == "__main__":
    app()
