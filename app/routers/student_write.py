from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_bank, get_concept_graph, get_store, require_student
from app.dto import from_repair_context, to_repair_context, vector_views
from app.schemas import (
    AnswerCheckView,
    AttemptOutcomeView,
    AttemptSubmitRequest,
    ReflectionStoredView,
    ReflectionSubmitRequest,
    StepCheckView,
    StuckPointView,
)
from backend.attempt_service import AttemptService, AttemptSubmission
from backend.item_bank import ItemBank
from backend.models import Track
from backend.persistence import LearningStore


router = APIRouter()


@router.post("/attempts", response_model=AttemptOutcomeView, status_code=status.HTTP_201_CREATED)
def submit_attempt(
    request: AttemptSubmitRequest,
    student_id: str = Depends(require_student),
    bank: ItemBank = Depends(get_bank),
    store: LearningStore = Depends(get_store),
    graph: dict = Depends(get_concept_graph),
) -> AttemptOutcomeView:
    item = _get_active_item(bank, request.item_id)
    track = Track(request.track)
    _validate_repair_context(track, request, bank)

    outcome = AttemptService(bank, store).submit(
        student_id=student_id,
        submission=AttemptSubmission(
            item_id=request.item_id,
            track=track,
            submitted_answer=request.submitted_answer,
            submitted_steps=tuple(request.submitted_steps),
            hint_level_used=request.hint_level_used,
            selected_error_code=request.selected_error_code,
            articulation_ok=request.articulation_ok,
            repair_context=to_repair_context(request.repair_context),
        ),
    )
    next_item_id, next_track = AttemptService(bank, store).next_item_after(outcome)
    attempt = outcome.recorded_attempt
    if attempt.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ATTEMPT_ID_MISSING", "message": "Attempt id was not populated.", "details": {}}},
        )

    return AttemptOutcomeView(
        attempt_id=attempt.id,
        item_id=outcome.item_id,
        correct=outcome.check.correct,
        feedback=outcome.check.feedback,
        selected_error_code=(None if outcome.stuck_point is None else outcome.stuck_point.error_code)
        or outcome.check.selected_error_code,
        path_match_status=attempt.path_match_status,
        answer_check=AnswerCheckView(
            correct=outcome.check.correct,
            method=outcome.check.method,
            feedback=outcome.check.feedback,
        ),
        stuck_point=None if outcome.stuck_point is None else StuckPointView(
            matched=outcome.stuck_point.matched,
            error_code=outcome.stuck_point.error_code,
            category=None if outcome.stuck_point.category is None else str(outcome.stuck_point.category),
            diagnostic_sentence=outcome.stuck_point.diagnostic_sentence,
            repair_node_ids=list(outcome.stuck_point.repair_node_ids),
            fallback=outcome.stuck_point.fallback,
        ),
        step_checks=[
            StepCheckView(
                submitted_index=check.submitted_index,
                submitted_text=check.submitted_text,
                status=check.status.value,
                expected_step_number=check.expected_step_number,
                diagnostic_target=check.diagnostic_target,
                diagnostic_sentence=check.diagnostic_sentence,
                selected_error_code=check.selected_error_code,
            )
            for check in outcome.step_checks
        ],
        next_item_id=next_item_id,
        next_track=next_track.value,
        repair_context_after=from_repair_context(outcome.repair_context_after),
        mastery_vectors=vector_views(
            outcome.mastery_vectors,
            graph,
            concept_ids=set(attempt.concept_ids),
        ),
    )


@router.post("/reflections", response_model=ReflectionStoredView, status_code=status.HTTP_201_CREATED)
def store_reflection(
    request: ReflectionSubmitRequest,
    student_id: str = Depends(require_student),
    bank: ItemBank = Depends(get_bank),
    store: LearningStore = Depends(get_store),
) -> ReflectionStoredView:
    _get_active_item(bank, request.item_id)
    if not request.reflection_text.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "EMPTY_REFLECTION",
                    "message": "Reflection text cannot be blank.",
                    "details": {},
                }
            },
        )
    store.add_reflection(
        student_id,
        request.item_id,
        request.reflection_text,
        request.articulation_ok,
        datetime.now(),
    )
    if request.articulation_ok is not None:
        store.update_latest_attempt_articulation(
            student_id,
            request.item_id,
            request.articulation_ok,
        )
    return ReflectionStoredView(stored=True)


def _validate_repair_context(track: Track, request: AttemptSubmitRequest, bank: ItemBank) -> None:
    if track == Track.REPAIR and request.repair_context is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "REPAIR_CONTEXT_MISSING",
                    "message": "Repair attempts require repair_context.",
                    "details": {},
                }
            },
        )
    if track != Track.REPAIR and request.repair_context is not None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "REPAIR_CONTEXT_UNEXPECTED",
                    "message": "repair_context is only valid for repair attempts.",
                    "details": {},
                }
            },
        )
    if request.repair_context is not None:
        try:
            bank.get(request.repair_context.original_item_id)
        except KeyError:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": {
                        "code": "ORIGINAL_ITEM_NOT_FOUND",
                        "message": "The original item in repair_context is not in the active bank.",
                        "details": {"item_id": request.repair_context.original_item_id},
                    }
                },
            ) from None


def _get_active_item(bank: ItemBank, item_id: str):
    try:
        item = bank.get(item_id)
    except KeyError:
        raise _item_not_found(item_id) from None
    if item.status != "active":
        raise _item_not_found(item_id)
    return item


def _item_not_found(item_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": f"Item {item_id} not found in active bank.",
                "details": {"item_id": item_id},
            }
        },
    )
