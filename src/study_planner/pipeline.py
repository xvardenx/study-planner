"""Coordinate daily inference, feasible decisions, and offline session placement."""

from dataclasses import dataclass
from datetime import date

from study_planner.calendar.schedule import (
    DailySchedule,
    days_until_exam,
    schedule_study_sessions,
    study_capacity,
)
from study_planner.planning import (
    DailyDecision,
    concept_priority,
    evaluate_daily_actions,
)
from study_planner.scenarios import ComprehensiveScenario, Scenario


@dataclass(frozen=True)
class DailyPlan:
    """A day's observed evidence, feasible recommendation, and placed sessions."""

    date: date
    evidence: Scenario
    available_study_hours: int
    decision: DailyDecision
    schedule: DailySchedule


def run_comprehensive_scenario(
    scenario: ComprehensiveScenario,
) -> tuple[DailyPlan, ...]:
    """Replay supplied observations without simulating learning or writing events.

    The same calendar snapshot constrains selection and placement. A shortfall
    therefore indicates inconsistent pipeline behavior, rather than a partial
    execution of an action whose expected outcomes were scored for more hours.
    """
    results = []
    for day in scenario.days:
        evidence = Scenario(
            days_until_exam(scenario.exam_date, day.date),
            scenario.concept_difficulties,
            day.concept_masteries,
            day.stress,
        )
        window = day.study_window
        capacity = study_capacity(day.busy_blocks, window.start, window.end)
        decision = evaluate_daily_actions(
            evidence.concept_difficulties,
            evidence.concept_masteries,
            evidence.stress,
            evidence.days_to_exam,
            available_study_hours=capacity,
        )
        schedule = schedule_study_sessions(
            decision.recommended.concept_hours,
            concept_priority(evidence.concept_difficulties, evidence.concept_masteries),
            day.busy_blocks,
            window.start,
            window.end,
        )
        if any(schedule.unscheduled_hours):
            raise RuntimeError(
                f"{day.date}: feasible recommendation could not be scheduled"
            )
        results.append(DailyPlan(day.date, evidence, capacity, decision, schedule))
    return tuple(results)
