from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import CONTENT_ROOT
from app.dependencies import get_bank, get_store, require_operator
from app.schemas import (
    AttemptHistoryListResponse,
    AttemptHistoryView,
    ErrorMappingView,
    HintRung,
    ItemBankEntryView,
    ItemBankGateStatus,
    ItemBankListResponse,
    ItemBankReloadResponse,
    ItemForOperator,
    SolutionStepView,
    UnmatchedPathsResponse,
    UnmatchedPathView,
    WeaknessReportOperatorView,
)
from backend.item_bank import ItemBank
from backend.persistence import LearningStore
from backend.weakness_report import build_weakness_report


router = APIRouter(prefix="/operator")


@router.get("/items", response_model=ItemBankListResponse)
def list_items(
    student_id: str = Depends(require_operator),
    bank: ItemBank = Depends(get_bank),
    store: LearningStore = Depends(get_store),
) -> ItemBankListResponse:
    attempts = store.list_attempts(student_id)
    attempts_by_item = defaultdict(list)
    for attempt in attempts:
        attempts_by_item[attempt.item_id].append(attempt)

    return ItemBankListResponse(
        items=[
            ItemBankEntryView(
                id=item.id,
                title=item.title,
                tier=item.tier,
                status=item.status,
                concept_ids=list(item.concept_ids),
                gates=_gates_for(item),
                attempt_count=len(item_attempts := attempts_by_item[item.id]),
                correct_ratio=_correct_ratio(item_attempts),
                avg_hint_level=_avg_correct_hint_level(item_attempts),
            )
            for item in bank.all()
        ]
    )


@router.get("/items/{item_id}", response_model=ItemForOperator)
def get_item(
    item_id: str,
    student_id: str = Depends(require_operator),
    bank: ItemBank = Depends(get_bank),
) -> ItemForOperator:
    try:
        item = bank.get(item_id)
    except KeyError:
        raise _item_not_found(item_id) from None
    return _item_for_operator(item)


@router.get("/attempts", response_model=AttemptHistoryListResponse)
def list_attempts(
    since: date | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    student_id: str = Depends(require_operator),
    store: LearningStore = Depends(get_store),
) -> AttemptHistoryListResponse:
    since_dt = datetime.combine(since, datetime.min.time()) if since else datetime.now() - timedelta(days=14)
    attempts = [attempt for attempt in store.list_attempts(student_id) if attempt.attempted_at >= since_dt]
    attempts = attempts[-limit:]
    return AttemptHistoryListResponse(attempts=[_attempt_view(attempt) for attempt in attempts])


@router.get("/weakness-report", response_model=WeaknessReportOperatorView)
def weakness_report(
    window_days: int = 14,
    as_of: date | None = None,
    student_id: str = Depends(require_operator),
    store: LearningStore = Depends(get_store),
) -> WeaknessReportOperatorView:
    generated_at = datetime.combine(as_of, datetime.max.time()) if as_of else datetime.now()
    report = build_weakness_report(
        student_id=student_id,
        attempts=store.list_attempts(student_id),
        generated_at=generated_at,
        window_days=window_days,
    )
    return WeaknessReportOperatorView(
        generated_at=report.generated_at,
        window_days=report.window_days,
        attempts_count=report.attempts_count,
        correct_count=report.correct_count,
        top_error_category=report.top_error_category,
        top_repair_node_id=report.top_repair_node_id,
        stuck_point_sentence=report.stuck_point_sentence,
        support_action_operator=report.support_action_operator,
        support_action_parent=report.support_action_parent,
    )


@router.get("/unmatched-paths", response_model=UnmatchedPathsResponse)
def unmatched_paths(
    since: date | None = None,
    student_id: str = Depends(require_operator),
    bank: ItemBank = Depends(get_bank),
    store: LearningStore = Depends(get_store),
) -> UnmatchedPathsResponse:
    since_dt = datetime.combine(since, datetime.min.time()) if since else None
    rows = store.list_unmatched_path_steps(student_id, since_dt)
    return UnmatchedPathsResponse(
        unmatched=[
            UnmatchedPathView(
                attempt_id=row.attempt_id,
                item_id=row.item_id,
                item_title=bank.get(row.item_id).title,
                attempted_at=row.attempted_at,
                submitted_steps=list(row.submitted_steps),
            )
            for row in rows
        ]
    )


@router.post("/item-bank/reload", response_model=ItemBankReloadResponse)
def reload_item_bank(
    request: Request,
    student_id: str = Depends(require_operator),
) -> ItemBankReloadResponse:
    bank = request.app.state.bank_holder.reload(CONTENT_ROOT)
    reloaded_at = datetime.now()
    request.app.state.bank_loaded_at = reloaded_at
    return ItemBankReloadResponse(
        reloaded_at=reloaded_at,
        item_bank={
            "extended": len(bank.by_tier("extended")),
            "core_repair": len(bank.by_tier("core_repair")),
        },
    )


def _gates_for(item) -> ItemBankGateStatus:
    gate = item.quality_gate()
    missing = set(gate["missing"])

    def status(field: str) -> str:
        return f"missing: {field}" if field in missing else "ok"

    return ItemBankGateStatus(
        concept_ids=status("concept_ids"),
        exam_literacy_ids=status("exam_literacy_ids"),
        prerequisite_ids=status("prerequisite_ids"),
        error_category_mapping=status("error_category_mapping"),
        hint_ladder=status("hint_ladder"),
        expected_solution_steps=status("expected_solution_steps"),
    )


def _correct_ratio(attempts) -> float:
    if not attempts:
        return 0.0
    return sum(attempt.correct for attempt in attempts) / len(attempts)


def _avg_correct_hint_level(attempts) -> float:
    correct = [attempt for attempt in attempts if attempt.correct]
    if not correct:
        return 0.0
    return sum(attempt.hint_level_used for attempt in correct) / len(correct)


def _item_for_operator(item) -> ItemForOperator:
    return ItemForOperator(
        id=item.id,
        title=item.title,
        tier=item.tier,
        status=item.status,
        student_facing_language=item.student_facing_language,
        metacognition_prompt=item.metacognition_prompt,
        transfer_variation_of=item.transfer_variation_of,
        source_reference=item.source_reference.model_dump(),
        exam_board=item.exam_board,
        syllabus_code=item.syllabus_code,
        tier_target=item.tier_target,
        paper_codes=list(item.paper_codes),
        syllabus_refs=list(item.syllabus_refs),
        source_style=item.source_style,
        year10_sequence_band=item.year10_sequence_band,
        transfer_axis=list(item.transfer_axis),
        problem_text=item.problem_text,
        student_prompt=item.student_prompt,
        expected_answer=item.expected_answer,
        marks=item.marks,
        difficulty=item.difficulty,
        calculator_policy=item.calculator_policy,
        notation_style=item.notation_style,
        concept_ids=list(item.concept_ids),
        exam_literacy_ids=list(item.exam_literacy_ids),
        prerequisite_ids=list(item.prerequisite_ids),
        error_category_mapping=[
            ErrorMappingView(
                code=mapping.code,
                category=mapping.category,
                trigger=mapping.trigger,
                expected_step_number=mapping.expected_step_number,
                diagnostic_target=mapping.diagnostic_target,
                diagnostic_sentence=mapping.diagnostic_sentence,
                repair_node_ids=list(mapping.repair_node_ids),
            )
            for mapping in item.error_category_mapping
        ],
        hint_ladder=[HintRung(level=hint.level, title=hint.title, prompt=hint.prompt) for hint in item.hint_ladder],
        expected_solution_steps=[
            SolutionStepView(
                step_number=step.step_number,
                action=step.action,
                expression=step.expression,
                diagnostic_target=step.diagnostic_target,
                common_errors=list(step.common_errors),
                diagnostic_sentence=step.diagnostic_sentence,
            )
            for step in item.expected_solution_steps
        ],
        accepted_alternative_paths=[path.model_dump() for path in item.accepted_alternative_paths],
        mark_scheme_notes=item.mark_scheme_notes,
        examiner_report_notes=item.examiner_report_notes,
    )


def _attempt_view(attempt) -> AttemptHistoryView:
    if attempt.id is None:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ATTEMPT_ID_MISSING", "message": "Attempt id is missing.", "details": {}}},
        )
    return AttemptHistoryView(
        id=attempt.id,
        item_id=attempt.item_id,
        track=attempt.track.value,
        correct=attempt.correct,
        hint_level_used=attempt.hint_level_used,
        attempted_at=attempt.attempted_at,
        error_category=attempt.error_category,
        diagnostic_target=attempt.diagnostic_target,
        diagnostic_sentence=attempt.diagnostic_sentence,
        repair_node_ids=list(attempt.repair_node_ids),
        path_match_status=attempt.path_match_status,
    )


def _item_not_found(item_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "error": {
                "code": "ITEM_NOT_FOUND",
                "message": f"Item {item_id} not found.",
                "details": {"item_id": item_id},
            }
        },
    )
