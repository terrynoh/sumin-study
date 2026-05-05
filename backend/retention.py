from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from backend.models import AttemptRecord, Track


@dataclass(frozen=True)
class RetentionDue:
    item_id: str
    concept_ids: tuple[str, ...]
    first_correct_date: date
    days_since: int
    reason: str


def due_retention_reviews(
    attempts: list[AttemptRecord],
    *,
    as_of: date,
    intervals: tuple[int, ...] = (3, 7, 14),
    limit: int = 3,
) -> list[RetentionDue]:
    """Return item-level retention checks due for v1.

    v1 uses fixed 3 / 7 / 14 day steps:
    - first correct Core attempt -> review after 3 days
    - passing a Review -> next review after 7 days
    - passing again -> next review after 14 days
    - failing Core/Review resets the schedule until the next correct Core.
    """

    due: list[RetentionDue] = []
    by_item: dict[str, list[AttemptRecord]] = {}
    for attempt in attempts:
        by_item.setdefault(attempt.item_id, []).append(attempt)

    for item_id, rows in by_item.items():
        rows = sorted(rows, key=lambda row: row.attempted_at)
        anchor = _latest_schedule_anchor(rows)
        if anchor is None:
            continue
        passed_reviews_after_anchor = [
            row for row in rows
            if row.track == Track.REVIEW and row.correct and row.attempted_at > anchor.attempted_at
        ]
        if len(passed_reviews_after_anchor) >= len(intervals):
            continue
        interval = intervals[len(passed_reviews_after_anchor)]
        due_date = anchor.attempted_at.date() + _days(interval)
        for review in passed_reviews_after_anchor:
            due_date = review.attempted_at.date() + _days(interval)
        if as_of < due_date:
            continue
        due.append(
            RetentionDue(
                item_id=item_id,
                concept_ids=anchor.concept_ids,
                first_correct_date=anchor.attempted_at.date(),
                days_since=(as_of - anchor.attempted_at.date()).days,
                reason=f"retention step due after {interval} days",
            )
        )

    due.sort(key=lambda item: (-item.days_since, item.item_id))
    return due[:limit]


def _latest_schedule_anchor(rows: list[AttemptRecord]) -> AttemptRecord | None:
    latest_failure_index = -1
    for index, row in enumerate(rows):
        if row.track in {Track.CORE, Track.REVIEW} and not row.correct:
            latest_failure_index = index
    for row in rows[latest_failure_index + 1:]:
        if row.track == Track.CORE and row.correct:
            return row
    return None


def _days(value: int):
    from datetime import timedelta

    return timedelta(days=value)
