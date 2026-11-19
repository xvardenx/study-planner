"""Behavioral tests for daily free time and study placement."""

from datetime import UTC, datetime, timedelta

import pytest

from study_planner.calendar.schedule import (
    TimeBlock,
    get_free_blocks,
    schedule_study_sessions,
)


def at(hour: int, minute: int = 0) -> datetime:
    """Build a fixed local test timestamp."""
    return datetime(2026, 11, 14, hour, minute)


def test_free_blocks_clip_merge_and_keep_exact_hour_gaps() -> None:
    """Ignore outside time and preserve a final gap at the minimum length."""
    busy = [
        TimeBlock(at(7), at(10)),
        TimeBlock(at(9, 30), at(11)),
        TimeBlock(at(10), at(12)),
        TimeBlock(at(14), at(15)),
        TimeBlock(at(18), at(19)),
    ]
    free = get_free_blocks(busy, at(9), at(16))
    assert [(block.start, block.end) for block in free] == [
        (at(12), at(14)),
        (at(15), at(16)),
    ]
    assert get_free_blocks([], at(9), at(10)) == [
        TimeBlock(at(9), at(10), title="Free")
    ]


def test_interval_validation_and_equal_start_sorting() -> None:
    """Reject invalid dates and avoid comparing display metadata when sorting."""
    with pytest.raises(ValueError):
        TimeBlock(at(10), at(10))
    with pytest.raises(ValueError):
        get_free_blocks([], at(10), at(9))
    with pytest.raises(ValueError):
        get_free_blocks([], at(9), at(10), timedelta(0))
    with pytest.raises(ValueError):
        get_free_blocks(
            [TimeBlock(at(9), at(10))],
            at(9).replace(tzinfo=UTC),
            at(11).replace(tzinfo=UTC),
        )
    assert (
        len(
            get_free_blocks(
                [TimeBlock(at(10), at(11), title="A"), TimeBlock(at(10), at(11))],
                at(9),
                at(12),
            )
        )
        == 2
    )


def test_rest_and_invalid_allocations() -> None:
    """Return an empty rest day and reject malformed allocation inputs."""
    rest = schedule_study_sessions((0, 0, 0), (0, 1, 2), [], at(9), at(17))
    assert rest.sessions == ()
    assert rest.unscheduled_hours == (0, 0, 0)
    with pytest.raises(ValueError):
        schedule_study_sessions((1, -1, 0), (0, 1, 2), [], at(9), at(17))
    with pytest.raises(ValueError):
        schedule_study_sessions((1, 1, 0), (0, 0, 2), [], at(9), at(17))


def test_priority_interleaving_and_preferred_breaks() -> None:
    """Start with the top concept, rotate, and keep 30-minute breaks."""
    result = schedule_study_sessions((2, 1, 1), (2, 0, 1), [], at(9), at(15))
    assert [block.concept_index for block in result.sessions] == [2, 0, 1, 0]
    assert [block.start for block in result.sessions] == [
        at(9),
        at(10, 30),
        at(12),
        at(13, 30),
    ]
    assert result.unscheduled_hours == (0, 0, 0)


def test_tight_window_reduces_breaks_before_dropping_hours() -> None:
    """Fit all hours when shorter breaks make the full allocation possible."""
    result = schedule_study_sessions((2, 1, 0), (0, 1, 2), [], at(9), at(12, 30))
    assert [block.start for block in result.sessions] == [
        at(9),
        at(10, 15),
        at(11, 30),
    ]
    assert [block.concept_index for block in result.sessions] == [0, 1, 0]
    assert result.unscheduled_hours == (0, 0, 0)


def test_partial_plan_keeps_higher_priority_hours_and_avoids_busy_time() -> None:
    """Report shortfalls and only place sessions in full free hours."""
    result = schedule_study_sessions(
        (2, 2, 1),
        (1, 0, 2),
        [TimeBlock(at(10), at(11)), TimeBlock(at(12), at(13))],
        at(9),
        at(14),
    )
    assert [block.concept_index for block in result.sessions] == [1, 0, 1]
    assert [block.start for block in result.sessions] == [at(9), at(11), at(13)]
    assert result.unscheduled_hours == (1, 0, 1)


def test_capacity_counts_whole_sessions_per_gap():
    """Disconnected short gaps cannot combine; overlaps are merged and clipped."""
    from study_planner.calendar.schedule import study_capacity

    assert study_capacity([TimeBlock(at(9, 30), at(10, 30))], at(9), at(11)) == 0
    busy = [
        TimeBlock(at(8), at(10)),
        TimeBlock(at(9), at(11)),
        TimeBlock(at(12, 30), at(14)),
    ]
    assert study_capacity(busy, at(9), at(16)) == 3
    assert study_capacity([], at(9), at(13)) == 4
