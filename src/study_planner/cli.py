"""Command-line access to the repository's example study scenarios."""

import typer
from rich.console import Console
from rich.rule import Rule
from rich.table import Table

from study_planner.pipeline import DailyPlan, run_comprehensive_scenario
from study_planner.planning import DailyDecision
from study_planner.scenarios import (
    Scenario,
    evaluate_scenario,
    load_all_scenarios,
    load_comprehensive_scenario,
)

app = typer.Typer(help="Evaluate example study-planning scenarios.")


def _show_scenario(
    console: Console, name: str, scenario: Scenario, decision: DailyDecision
) -> None:
    """Display supplied evidence and decision results without rerunning inference."""
    console.print(Rule(name, style="cyan"))
    days_to_exam_display = "day" if scenario.days_to_exam == 1 else "days"
    console.print(
        f"Exam in {scenario.days_to_exam} {days_to_exam_display}  •  Stress: {scenario.stress}  •  "
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
        _show_scenario(console, name, scenario, evaluate_scenario(scenario))


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
    _show_scenario(Console(), name, scenarios[name], evaluate_scenario(scenarios[name]))


def _show_daily_plan(console: Console, plan: DailyPlan) -> None:
    """Show one replay date's capacity, recommendation, and assigned sessions."""
    _show_scenario(console, plan.date.isoformat(), plan.evidence, plan.decision)
    console.print(f"Available study capacity: {plan.available_study_hours} hours")
    console.print(
        f"Recommended hours: {plan.decision.recommended.study_hours}  •  "
        f"Scheduled hours: {len(plan.schedule.sessions)}"
    )
    if not plan.schedule.sessions:
        console.print("No study sessions assigned.")
        return
    table = Table(title="Assigned study sessions")
    table.add_column("Start")
    table.add_column("End")
    table.add_column("Concept")
    for session in plan.schedule.sessions:
        if session.concept_index is None:
            raise ValueError("assigned study sessions must have a concept index")
        table.add_row(
            session.start.strftime("%H:%M:%S"),
            session.end.strftime("%H:%M:%S"),
            str(session.concept_index + 1),
        )
    console.print(table)


@app.command(name="run-comp")
def run_comprehensive(name: str) -> None:
    """Replay each pre-exam day through inference, selection, and scheduling."""
    try:
        scenario = load_comprehensive_scenario(name)
    except FileNotFoundError as error:
        raise typer.BadParameter(
            f"Unknown comprehensive scenario '{name}'.", param_hint="NAME"
        ) from error
    except ValueError as error:
        raise typer.BadParameter(str(error), param_hint="NAME") from error
    results = run_comprehensive_scenario(scenario)
    console = Console()
    for plan in results:
        _show_daily_plan(console, plan)


if __name__ == "__main__":
    app()
