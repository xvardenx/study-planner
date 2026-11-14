from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(order=True)
class TimeBlock:
    start: datetime
    end: datetime
    title: str | None = None
    description: str | None = None

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


def get_free_blocks(
    schedule: list[TimeBlock],
    window_start: datetime,
    window_end: datetime,
    min_duration: timedelta = timedelta(hours=1),
) -> list[TimeBlock]:

    sorted_busy = sorted(schedule)

    merged = []
    for block in sorted_busy:
        if not merged or block.start > merged[-1].end:
            merged.append(TimeBlock(block.start, block.end))
        else:
            merged[-1].end = max(merged[-1].end, block.end)

    free_blocks = []
    cursor = window_start

    for busy in merged:
        if busy.end <= cursor:
            continue
        if busy.start > cursor:
            gap_end = min(busy.start, window_end)
            if gap_end - cursor >= min_duration:
                free_blocks.append(TimeBlock(start=cursor, end=gap_end, title="Free"))
        cursor = max(cursor, busy.end)
        if cursor >= window_end:
            break

    if cursor < window_end and (window_end - cursor) > min_duration:
        free_blocks.append(TimeBlock(start=cursor, end=window_end, title="Free"))

    return free_blocks
