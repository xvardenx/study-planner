"""End-to-end daily decision and scheduling checks for scenario replay."""

from dataclasses import replace
from datetime import timedelta

import pytest

from study_planner import pipeline
from study_planner.calendar.schedule import DailySchedule
from study_planner.pipeline import run_comprehensive_scenario
from study_planner.planning import DailyAction, evaluate_daily_actions
from study_planner.scenarios import load_comprehensive_scenario


def test_complete_replay_schedules_feasible_actions_and_supplied_evidence():
    """Every pre-exam day uses its observations and places its full allocation."""
    scenario = load_comprehensive_scenario("progressing")
    results = run_comprehensive_scenario(scenario)
    assert len(results) == 6
    assert [plan.evidence.days_to_exam for plan in results] == [6, 5, 4, 3, 2, 1]
    first = results[0]
    unconstrained = evaluate_daily_actions(
        first.evidence.concept_difficulties,
        first.evidence.concept_masteries,
        first.evidence.stress,
        first.evidence.days_to_exam,
    )
    assert first.available_study_hours == 2
    assert unconstrained.recommended.study_hours > 2
    assert first.decision.recommended.study_hours <= 2
    for day, plan in zip(scenario.days, results, strict=True):
        assert plan.date < scenario.exam_date
        assert plan.evidence.concept_masteries == day.concept_masteries
        assert plan.evidence.stress == day.stress
        assert len(plan.schedule.sessions) == plan.decision.recommended.study_hours
        assert plan.schedule.unscheduled_hours == (0, 0, 0)
        assert (
            tuple(
                sum(
                    session.concept_index == index for session in plan.schedule.sessions
                )
                for index in range(3)
            )
            == plan.decision.recommended.concept_hours
        )
        for session in plan.schedule.sessions:
            assert session.duration == timedelta(hours=1)
            assert (
                day.study_window.start
                <= session.start
                < session.end
                <= day.study_window.end
            )
            assert all(
                session.end <= busy.start or session.start >= busy.end
                for busy in day.busy_blocks
            )
        assert all(
            a.end <= b.start
            for a, b in zip(plan.schedule.sessions, plan.schedule.sessions[1:])
        )


def test_fully_busy_day_selects_rest_without_changing_tomorrow():
    """No capacity forces rest while tomorrow retains its supplied evidence."""
    scenario = load_comprehensive_scenario("progressing")
    first = scenario.days[0]
    first = replace(first, busy_blocks=(first.study_window,))
    scenario = replace(scenario, days=(first, *scenario.days[1:]))
    results = run_comprehensive_scenario(scenario)
    assert results[0].decision.recommended.action is DailyAction.REST
    assert results[0].schedule.sessions == ()
    assert results[1].evidence.concept_masteries == scenario.days[1].concept_masteries


def test_pipeline_rejects_internal_scheduling_shortfall(monkeypatch):
    """A feasible choice must never be silently presented as partially executed."""
    monkeypatch.setattr(
        pipeline, "schedule_study_sessions", lambda *args: DailySchedule((), (1, 0, 0))
    )
    with pytest.raises(RuntimeError, match="2026-11-16"):
        run_comprehensive_scenario(load_comprehensive_scenario("progressing"))
