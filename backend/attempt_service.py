from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from backend.answer_checker import AnswerCheckResult, check_answer
from backend.item_bank import ItemBank
from backend.mastery import calculate_mastery_vectors
from backend.models import AttemptRecord, MasteryVector, RepairContext, Track
from backend.persistence import LearningStore
from backend.session_engine import SessionEngine
from backend.step_checker import StepCheck, StepStatus, check_submitted_steps, first_error_code_from_steps
from schema.stuck_point import StudentAttempt, StudentStep, StuckPointMatch, match_stuck_point


@dataclass(frozen=True)
class AttemptSubmission:
    item_id: str
    track: Track
    submitted_answer: str
    submitted_steps: tuple[str, ...] = ()
    hint_level_used: int = 0
    selected_error_code: str | None = None
    articulation_ok: bool | None = None
    repair_context: RepairContext | None = None


@dataclass(frozen=True)
class AttemptOutcome:
    item_id: str
    check: AnswerCheckResult
    step_checks: tuple[StepCheck, ...]
    stuck_point: StuckPointMatch | None
    recorded_attempt: AttemptRecord
    next_track: Track
    mastery_vectors: dict[str, MasteryVector]
    repair_context_after: RepairContext | None
    next_item_override: tuple[str, Track] | None = None


class AttemptService:
    def __init__(self, item_bank: ItemBank, store: LearningStore) -> None:
        self.item_bank = item_bank
        self.store = store
        self.session_engine = SessionEngine(item_bank)

    def submit(
        self,
        *,
        student_id: str,
        submission: AttemptSubmission,
        attempted_at: datetime | None = None,
    ) -> AttemptOutcome:
        attempted_at = attempted_at or datetime.now()
        item = self.item_bank.get(submission.item_id)
        check = check_answer(item, submission.submitted_answer)
        step_checks = check_submitted_steps(item, submission.submitted_steps)
        selected_error_code = (
            submission.selected_error_code
            or check.selected_error_code
            or first_error_code_from_steps(step_checks)
        )

        stuck_point = None
        if not check.correct:
            stuck_point = match_stuck_point(
                item,
                StudentAttempt(
                    item_id=item.id,
                    final_answer=submission.submitted_answer,
                    submitted_steps=tuple(
                        StudentStep(step_number=index + 1, text=text)
                        for index, text in enumerate(submission.submitted_steps)
                    ),
                    selected_error_code=selected_error_code,
                    hint_level_used=submission.hint_level_used,
                ),
            )

        attempt = AttemptRecord(
            item_id=item.id,
            concept_ids=tuple(item.concept_ids),
            track=submission.track,
            correct=check.correct,
            hint_level_used=submission.hint_level_used,
            attempted_at=attempted_at,
            error_category=None if check.correct or stuck_point is None else stuck_point.category,
            diagnostic_target=None if check.correct or stuck_point is None else stuck_point.diagnostic_target,
            diagnostic_sentence=None if check.correct or stuck_point is None else stuck_point.diagnostic_sentence,
            repair_node_ids=() if check.correct or stuck_point is None else tuple(stuck_point.repair_node_ids),
            transfer_variation_of=item.transfer_variation_of,
            articulation_ok=submission.articulation_ok,
            path_match_status=self._path_match_status(item, check.correct, step_checks),
        )
        attempt_id = self.store.add_attempt(student_id, attempt)
        attempt = replace(attempt, id=attempt_id)
        if attempt.path_match_status == "unmatched":
            self.store.add_unmatched_path_steps(
                student_id,
                attempt_id,
                item.id,
                tuple(submission.submitted_steps),
                attempt.attempted_at,
            )

        attempts = self.store.list_attempts(student_id)
        next_track = self.session_engine.route_after_attempt(attempt)
        repair_context_after = self._next_repair_context(submission, attempt, next_track)
        next_item_override = self._next_item_override(submission, attempt, repair_context_after)
        mastery_vectors = calculate_mastery_vectors(attempts)

        return AttemptOutcome(
            item_id=item.id,
            check=check,
            step_checks=step_checks,
            stuck_point=stuck_point,
            recorded_attempt=attempt,
            next_track=next_track,
            mastery_vectors=mastery_vectors,
            repair_context_after=repair_context_after,
            next_item_override=next_item_override,
        )

    def next_item_after(self, outcome: AttemptOutcome) -> tuple[str, Track]:
        if outcome.next_item_override is not None:
            return outcome.next_item_override
        context = outcome.repair_context_after
        if context is None:
            return (outcome.item_id, outcome.next_track)
        if context.escalated:
            return (context.original_item_id, context.original_track)
        if outcome.next_track == Track.REPAIR:
            repair_nodes = outcome.recorded_attempt.repair_node_ids
            for node_id in repair_nodes:
                for item in self.item_bank.core_repair_items_for(node_id):
                    if item.id not in context.repair_chain:
                        return (item.id, Track.REPAIR)
            return (context.original_item_id, context.original_track)
        return (context.original_item_id, context.original_track)

    def _next_repair_context(
        self,
        submission: AttemptSubmission,
        attempt: AttemptRecord,
        next_track: Track,
    ) -> RepairContext | None:
        context = submission.repair_context
        if context is not None and attempt.track == Track.REPAIR and attempt.correct:
            return None
        if context is not None and attempt.track == Track.REPAIR and not attempt.correct:
            chain = context.repair_chain + (attempt.item_id,)
            depth = context.depth + 1
            return RepairContext(
                original_item_id=context.original_item_id,
                original_track=context.original_track,
                repair_chain=chain,
                depth=depth,
                escalated=depth >= 3,
            )
        if next_track == Track.REPAIR:
            return RepairContext(
                original_item_id=attempt.item_id,
                original_track=attempt.track,
                repair_chain=(),
                depth=0,
                escalated=False,
            )
        return None

    def _next_item_override(
        self,
        submission: AttemptSubmission,
        attempt: AttemptRecord,
        repair_context_after: RepairContext | None,
    ) -> tuple[str, Track] | None:
        context = submission.repair_context
        if context is not None and attempt.track == Track.REPAIR and attempt.correct:
            return (context.original_item_id, context.original_track)
        if repair_context_after is not None and repair_context_after.escalated:
            return (repair_context_after.original_item_id, repair_context_after.original_track)
        return None

    def _path_match_status(self, item, correct: bool, step_checks: tuple[StepCheck, ...]) -> str:
        if not correct:
            return "n/a"
        if self._matches_alternative_path(item, step_checks):
            return "alternative"
        if any(check.status == StepStatus.UNMATCHED for check in step_checks):
            return "unmatched"
        if all(check.status == StepStatus.MATCHED_EXPECTED for check in step_checks):
            return "matched"
        return "n/a"

    def _matches_alternative_path(self, item, step_checks: tuple[StepCheck, ...]) -> bool:
        if not item.accepted_alternative_paths or not step_checks:
            return False
        submitted = tuple(check.submitted_text.strip().lower() for check in step_checks)
        for path in item.accepted_alternative_paths:
            expected = tuple(step.expression.strip().lower() for step in path.steps)
            if submitted == expected:
                return True
        return False
