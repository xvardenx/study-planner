import typer

from study_planner.planning import DailyDecision
from study_planner.scenarios import evaluate_scenario, load_all_scenarios

app = typer.Typer()


@app.command()
def status():
    """Placeholder so that a specific command has to be ran."""
    typer.echo("Status:OK")


@app.command(name="all")
def run_all_scenarios():
    """Runs inference and displays results for all scenarios."""
    typer.echo("Running all scenarios")

    scenarios = load_all_scenarios()
    for name, scenario in scenarios.items():
        decision: DailyDecision = evaluate_scenario(scenario)

        typer.echo(f"\n{name}")
        typer.echo(
            f"  Days to exam: {scenario.days_to_exam}; stress: {scenario.stress}"
        )
        typer.echo(f"  Difficulties: {', '.join(scenario.concept_difficulties)}")
        typer.echo(f"  Masteries:    {', '.join(scenario.concept_masteries)}")
        typer.echo(
            f"  Baseline exam success: {decision.baseline_success_probability:.1%}"
        )
        typer.echo(
            "  Action             Hours  Concept hours  Expected success  Stress  Utility"
        )
        for evaluation in decision.evaluations:
            typer.echo(
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
            typer.echo(f"  Stress-aware study limit: {limit} hours")
        typer.echo(f"  Recommended: {decision.recommended.action.value}")


if __name__ == "__main__":
    app()
