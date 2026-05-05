from __future__ import annotations

from collections import Counter
from datetime import date

from backend.item_bank import ItemBank
from backend.mastery import calculate_mastery_vectors
from backend.models import AttemptRecord, DailySessionPlan, DimensionState, SessionTask, Track
from backend.retention import due_retention_reviews


class SessionEngine:
    def __init__(self, item_bank: ItemBank) -> None:
        self.item_bank = item_bank

    def build_daily_plan(
        self,
        *,
        student_id: str,
        session_date: date,
        attempts: list[AttemptRecord],
        core_count: int = 3,
    ) -> DailySessionPlan:
        seen_item_ids = {attempt.item_id for attempt in attempts}
        mastery = calculate_mastery_vectors(attempts)

        review = self._select_review_tasks(attempts, session_date)
        repair = self._select_repair_tasks(attempts)
        core = self._select_core_tasks(seen_item_ids, mastery, limit=core_count)

        explore_locked = not self._has_core_success_today(attempts, session_date)
        explore = self._select_explore_tasks(seen_item_ids, locked=explore_locked)
        stretch_locked = not any(vector.mastered for vector in mastery.values())
        stretch = self._select_stretch_tasks(seen_item_ids, locked=stretch_locked)

        notes = []
        if repair:
            notes.append("Repair is available because recent attempts exposed a prerequisite gap.")
        if explore_locked:
            notes.append("Explore unlocks after at least one Core success today.")
        if stretch_locked:
            notes.append("Stretch unlocks after stable mastery evidence.")

        return DailySessionPlan(
            student_id=student_id,
            session_date=session_date,
            review=tuple(review),
            core=tuple(core),
            repair=tuple(repair),
            explore=tuple(explore),
            stretch=tuple(stretch),
            notes=tuple(notes),
        )

    def route_after_attempt(self, attempt: AttemptRecord, consecutive_incorrect_same_concept: int = 1) -> Track:
        if attempt.track in {Track.EXPLORE, Track.STRETCH}:
            return Track.CORE
        if attempt.correct:
            return Track.CORE
        if attempt.repair_node_ids or consecutive_incorrect_same_concept >= 2:
            return Track.REPAIR
        return Track.CORE

    def _select_core_tasks(
        self,
        seen_item_ids: set[str],
        mastery: dict[str, object],
        *,
        limit: int,
    ) -> list[SessionTask]:
        extended_items = [item for item in self.item_bank.by_tier("extended") if self._is_core_path_item(item)]
        items = [item for item in extended_items if item.id not in seen_item_ids][:limit]
        if len(items) < limit:
            for item in extended_items:
                if item in items:
                    continue
                if any(
                    mastery.get(concept_id)
                    and getattr(mastery[concept_id], "accuracy") != DimensionState.READY
                    for concept_id in item.concept_ids
                ):
                    items.append(item)
                if len(items) == limit:
                    break
        return [
            SessionTask(
                track=Track.CORE,
                item_id=item.id,
                reason="next active Core item" if item.id not in seen_item_ids else "concept still developing",
                concept_ids=tuple(item.concept_ids),
            )
            for item in items[:limit]
        ]

    def _is_core_path_item(self, item) -> bool:
        return getattr(item, "year10_sequence_band", "core_target") in {"core_target", "transfer"}

    def _select_repair_tasks(self, attempts: list[AttemptRecord]) -> list[SessionTask]:
        recent_failures = [attempt for attempt in attempts[-6:] if not attempt.correct and attempt.repair_node_ids]
        if not recent_failures:
            return []
        repair_counts: Counter[str] = Counter()
        for attempt in recent_failures:
            repair_counts.update(attempt.repair_node_ids)
        repair_node, _ = repair_counts.most_common(1)[0]
        core_repair_items = self.item_bank.core_repair_items_for(repair_node)
        if core_repair_items:
            seen_repair_ids = {attempt.item_id for attempt in attempts if attempt.track == Track.REPAIR}
            selected = next((item for item in core_repair_items if item.id not in seen_repair_ids), core_repair_items[0])
            return [
                SessionTask(
                    track=Track.REPAIR,
                    item_id=selected.id,
                    reason=f"core_repair route for {repair_node}",
                    concept_ids=tuple(selected.concept_ids),
                )
            ]
        for item in self.item_bank.all():
            refs = set(item.concept_ids + item.prerequisite_ids + item.exam_literacy_ids)
            if repair_node in refs:
                return [
                    SessionTask(
                        track=Track.REPAIR,
                        item_id=item.id,
                        reason=f"core_repair pool empty for {repair_node}; fallback extended item",
                        concept_ids=tuple(item.concept_ids),
                    )
                ]
        return []

    def _select_review_tasks(self, attempts: list[AttemptRecord], session_date: date) -> list[SessionTask]:
        due = due_retention_reviews(attempts, as_of=session_date, limit=2)
        if not due:
            return []
        return [
            SessionTask(
                track=Track.REVIEW,
                item_id=item.item_id,
                reason=item.reason,
                concept_ids=item.concept_ids,
            )
            for item in due
        ]

    def _select_explore_tasks(self, seen_item_ids: set[str], *, locked: bool) -> list[SessionTask]:
        for item in self.item_bank.by_tier("extended"):
            if item.transfer_variation_of and item.id not in seen_item_ids:
                return [
                    SessionTask(
                        track=Track.EXPLORE,
                        item_id=item.id,
                        reason="transfer variation",
                        concept_ids=tuple(item.concept_ids),
                        locked=locked,
                    )
                ]
        return []

    def _select_stretch_tasks(self, seen_item_ids: set[str], *, locked: bool) -> list[SessionTask]:
        for item in reversed(self.item_bank.by_tier("extended")):
            if item.difficulty >= 4 and item.id not in seen_item_ids:
                return [
                    SessionTask(
                        track=Track.STRETCH,
                        item_id=item.id,
                        reason="higher-difficulty extension",
                        concept_ids=tuple(item.concept_ids),
                        locked=locked,
                    )
                ]
        return []

    def _has_core_success_today(self, attempts: list[AttemptRecord], session_date: date) -> bool:
        return any(
            attempt.track == Track.CORE and attempt.correct and attempt.attempted_at.date() == session_date
            for attempt in attempts
        )
