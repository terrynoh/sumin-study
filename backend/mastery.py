"""Mastery vector calculation.

v1 mastery dimension stability policy: see DESIGN_BRIEF §5.
Each dimension's drop behavior is intentional:
- accuracy uses a 4-attempt rolling window
- hint_independence reflects the most recent correct attempt
- retention/transfer remain stable once ready unless explicit review failure
  handling is added later
- articulation tracks the latest reflection sample
v2 may revisit drop strictness.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from backend.models import AttemptRecord, DimensionState, MasteryVector, Track


def calculate_mastery_vectors(attempts: list[AttemptRecord]) -> dict[str, MasteryVector]:
    by_concept: dict[str, list[AttemptRecord]] = defaultdict(list)
    for attempt in sorted(attempts, key=lambda item: item.attempted_at):
        for concept_id in attempt.concept_ids:
            by_concept[concept_id].append(attempt)

    return {concept_id: _calculate_for_concept(concept_id, rows) for concept_id, rows in by_concept.items()}


def _calculate_for_concept(concept_id: str, attempts: list[AttemptRecord]) -> MasteryVector:
    scored = [row for row in attempts if row.track in {Track.CORE, Track.REVIEW}]
    recent = scored[-4:]

    if len(recent) >= 4 and sum(row.correct for row in recent) >= 3:
        accuracy = DimensionState.READY
    elif scored:
        accuracy = DimensionState.DEVELOPING
    else:
        accuracy = DimensionState.NOT_CHECKED

    latest_correct = next((row for row in reversed(scored) if row.correct), None)
    if latest_correct and latest_correct.hint_level_used <= 1:
        hint_independence = DimensionState.READY
    elif scored:
        hint_independence = DimensionState.DEVELOPING
    else:
        hint_independence = DimensionState.NOT_CHECKED

    review_success = any(row.track == Track.REVIEW and row.correct for row in scored)
    retention_due_success = _has_retention_success(scored)
    if review_success or retention_due_success:
        retention = DimensionState.READY
    elif scored:
        retention = DimensionState.DEVELOPING
    else:
        retention = DimensionState.NOT_CHECKED

    transfer_success = any(row.correct and row.transfer_variation_of for row in scored)
    if transfer_success:
        transfer = DimensionState.READY
    elif scored:
        transfer = DimensionState.DEVELOPING
    else:
        transfer = DimensionState.NOT_CHECKED

    articulation_values = [row.articulation_ok for row in attempts if row.articulation_ok is not None]
    if articulation_values and articulation_values[-1]:
        articulation = DimensionState.READY
    elif articulation_values:
        articulation = DimensionState.DEVELOPING
    else:
        articulation = DimensionState.NOT_CHECKED

    return MasteryVector(
        concept_id=concept_id,
        accuracy=accuracy,
        hint_independence=hint_independence,
        retention=retention,
        transfer=transfer,
        articulation=articulation,
    )


def _has_retention_success(attempts: list[AttemptRecord]) -> bool:
    correct_attempts = [row for row in attempts if row.correct]
    for later in correct_attempts:
        for earlier in correct_attempts:
            if later.attempted_at - earlier.attempted_at >= timedelta(days=3):
                return True
    return False
