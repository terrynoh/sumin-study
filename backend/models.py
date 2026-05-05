from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class Track(StrEnum):
    CORE = "core"
    REPAIR = "repair"
    EXPLORE = "explore"
    STRETCH = "stretch"
    REVIEW = "review"


@dataclass(frozen=True)
class RepairContext:
    original_item_id: str
    original_track: Track
    repair_chain: tuple[str, ...] = ()
    depth: int = 0
    escalated: bool = False


class DimensionState(StrEnum):
    READY = "ready"
    DEVELOPING = "developing"
    NOT_CHECKED = "not_checked"


@dataclass(frozen=True)
class AttemptRecord:
    item_id: str
    concept_ids: tuple[str, ...]
    track: Track
    correct: bool
    hint_level_used: int
    attempted_at: datetime
    error_category: str | None = None
    diagnostic_target: str | None = None
    diagnostic_sentence: str | None = None
    repair_node_ids: tuple[str, ...] = ()
    transfer_variation_of: str | None = None
    articulation_ok: bool | None = None
    id: int | None = None
    path_match_status: str = "n/a"


@dataclass(frozen=True)
class Reflection:
    student_id: str
    item_id: str
    reflection_text: str
    articulation_ok: bool | None
    submitted_at: datetime
    id: int | None = None


@dataclass(frozen=True)
class ParentSummary:
    student_id: str
    week_start: date
    week_end: date
    improving: str
    still_developing: str
    one_thing_that_would_help: str
    created_at: datetime
    sent_at: datetime | None = None
    id: int | None = None


@dataclass(frozen=True)
class UnmatchedPathRecord:
    attempt_id: int
    item_id: str
    submitted_steps: tuple[str, ...]
    attempted_at: datetime
    id: int | None = None


@dataclass(frozen=True)
class MasteryVector:
    concept_id: str
    accuracy: DimensionState = DimensionState.NOT_CHECKED
    hint_independence: DimensionState = DimensionState.NOT_CHECKED
    retention: DimensionState = DimensionState.NOT_CHECKED
    transfer: DimensionState = DimensionState.NOT_CHECKED
    articulation: DimensionState = DimensionState.NOT_CHECKED

    @property
    def mastered(self) -> bool:
        return all(
            state == DimensionState.READY
            for state in (
                self.accuracy,
                self.hint_independence,
                self.retention,
                self.transfer,
                self.articulation,
            )
        )


@dataclass(frozen=True)
class SessionTask:
    track: Track
    item_id: str
    reason: str
    concept_ids: tuple[str, ...]
    locked: bool = False


@dataclass(frozen=True)
class DailySessionPlan:
    student_id: str
    session_date: date
    core: tuple[SessionTask, ...]
    repair: tuple[SessionTask, ...] = ()
    review: tuple[SessionTask, ...] = ()
    explore: tuple[SessionTask, ...] = ()
    stretch: tuple[SessionTask, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def tasks(self) -> tuple[SessionTask, ...]:
        return self.core + self.review + self.repair + self.explore + self.stretch


@dataclass
class ConceptMasterySnapshot:
    student_id: str
    concept_vectors: dict[str, MasteryVector] = field(default_factory=dict)


@dataclass(frozen=True)
class WeaknessReport:
    student_id: str
    generated_at: datetime
    window_days: int
    attempts_count: int
    correct_count: int
    top_error_category: str | None
    top_repair_node_id: str | None
    stuck_point_sentence: str
    support_action_operator: str
    support_action_parent: str
