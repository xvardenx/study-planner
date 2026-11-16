"""Free-time discovery and placement of one day's study sessions."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

SESSION_DURATION = timedelta(hours=1)
PREFERRED_BREAK = timedelta(minutes=30)


@dataclass(order=True, frozen=True)
class TimeBlock:
    """A half-open calendar interval; study blocks carry a concept index."""

    start: datetime
    end: datetime
    title: str | None = field(default=None, compare=False)
    description: str | None = field(default=None, compare=False)
    concept_index: int | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Reject empty intervals and incomparable datetime values."""
        try:
            valid = self.start < self.end
        except TypeError as exc:
            raise ValueError("block datetimes must be comparable") from exc
        if not valid:
            raise ValueError("block start must precede end")

    @property
    def duration(self) -> timedelta:
        """Return the length of the interval."""
        return self.end - self.start


@dataclass(frozen=True)
class DailySchedule:
    """Placed study sessions and hours left over for each of three concepts."""

    sessions: tuple[TimeBlock, ...]
    unscheduled_hours: tuple[int, int, int]


def days_until_exam(exam_date: date, start_date: date | None = None) -> int:
    """Returns the number of days until the exam. `start_date` defaults to today if not passed."""
    if start_date is None:
        start_date = date.today()
    if exam_date <= start_date:
        raise ValueError("exam date must come after the start date")

    return (exam_date - start_date).days


def get_free_blocks(
    schedule: Sequence[TimeBlock],
    window_start: datetime,
    window_end: datetime,
    min_duration: timedelta = SESSION_DURATION,
) -> list[TimeBlock]:
    """Return usable gaps after clipping and merging busy calendar intervals."""
    try:
        valid_window = window_start < window_end
    except TypeError as exc:
        raise ValueError("window datetimes must be comparable") from exc
    if not valid_window:
        raise ValueError("window start must precede end")
    if min_duration <= timedelta(0):
        raise ValueError("minimum duration must be positive")

    try:
        clipped = sorted(
            (
                max(block.start, window_start),
                min(block.end, window_end),
            )
            for block in schedule
        )
    except TypeError as exc:
        raise ValueError("busy and window datetimes must be comparable") from exc

    free_blocks: list[TimeBlock] = []
    cursor = window_start
    for start, end in clipped:
        if start >= end:
            continue
        if start > cursor and start - cursor >= min_duration:
            free_blocks.append(TimeBlock(cursor, start, title="Free"))
        cursor = max(cursor, end)
    if window_end - cursor >= min_duration:
        free_blocks.append(TimeBlock(cursor, window_end, title="Free"))
    return free_blocks


def _place_sessions(
    concepts: Sequence[int], free_blocks: Sequence[TimeBlock], gap: timedelta
) -> tuple[TimeBlock, ...] | None:
    """Place ordered one-hour sessions at their earliest feasible starts."""
    sessions: list[TimeBlock] = []
    block_index = 0
    for concept in concepts:
        while block_index < len(free_blocks):
            block = free_blocks[block_index]
            start = block.start
            if sessions:
                start = max(start, sessions[-1].end + gap)
            end = start + SESSION_DURATION
            if end <= block.end:
                sessions.append(
                    TimeBlock(
                        start,
                        end,
                        title=f"Study concept {concept + 1}",
                        concept_index=concept,
                    )
                )
                break
            block_index += 1
        else:
            return None
    return tuple(sessions)


def schedule_study_sessions(
    concept_hours: Sequence[int],
    concept_priority: Sequence[int],
    busy_blocks: Sequence[TimeBlock],
    window_start: datetime,
    window_end: datetime,
) -> DailySchedule:
    """Place as many priority hours as possible, favoring 30-minute breaks.

    Capacity is calculated without breaks, so a preferred break never causes
    an otherwise schedulable hour to be dropped. Sessions for retained hours
    are interleaved by concept priority. Breaks are maximized to whole seconds
    up to 30 minutes, then sessions are placed as early as possible.
    """
    if len(concept_hours) != 3 or any(
        type(hours) is not int or hours < 0 for hours in concept_hours
    ):
        raise ValueError("concept hours must be three nonnegative integers")
    if len(concept_priority) != 3 or set(concept_priority) != {0, 1, 2}:
        raise ValueError("concept priority must order indices 0, 1, and 2")
    hours = (concept_hours[0], concept_hours[1], concept_hours[2])

    free_blocks = get_free_blocks(busy_blocks, window_start, window_end)
    capacity = sum(block.duration // SESSION_DURATION for block in free_blocks)
    remaining_capacity = capacity
    selected = [0, 0, 0]
    for concept in concept_priority:
        selected[concept] = min(concept_hours[concept], remaining_capacity)
        remaining_capacity -= selected[concept]

    ordered = [
        concept
        for round_index in range(max(selected, default=0))
        for concept in concept_priority
        if round_index < selected[concept]
    ]
    if not ordered:
        return DailySchedule((), hours)

    low, high = 0, int(PREFERRED_BREAK.total_seconds())
    while low < high:
        midpoint = (low + high + 1) // 2
        if _place_sessions(ordered, free_blocks, timedelta(seconds=midpoint)):
            low = midpoint
        else:
            high = midpoint - 1
    sessions = _place_sessions(ordered, free_blocks, timedelta(seconds=low))
    assert sessions is not None  # Capacity guarantees placement with no breaks.
    shortfall = (
        hours[0] - selected[0],
        hours[1] - selected[1],
        hours[2] - selected[2],
    )
    return DailySchedule(sessions, shortfall)
