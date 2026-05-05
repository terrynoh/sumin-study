from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_bank, get_concept_graph, get_store, require_student
from app.dto import vector_views
from app.schemas import (
    DailySessionPlanView,
    HintRung,
    ItemForStudent,
    MasterySnapshotView,
    MasteryVectorView,
    RetentionDueResponse,
    RetentionDueView,
    SessionTaskView,
    WeaknessReportStudentView,
)
from backend.item_bank import ItemBank
from backend.mastery import calculate_mastery_vectors
from backend.persistence import LearningStore
from backend.retention import due_retention_reviews
from backend.session_engine import SessionEngine
from backend.weakness_report import build_weakness_report


router = APIRouter()


@router.get("/items/{item_id}", response_model=ItemForStudent)
def get_item_for_student(
    item_id: str,
    student_id: str = Depends(require_student),
    bank: ItemBank = Depends(get_bank),
) -> ItemForStudent:
    try:
        item = bank.get(item_id)
    except KeyError:
        raise _item_not_found(item_id) from None
    if item.status != "active":
        raise _item_not_found(item_id)
    return ItemForStudent(
        id=item.id,
        title=item.title,
        tier=item.tier,
        student_facing_language=item.student_facing_language,
        problem_text=item.problem_text,
        student_prompt=item.student_prompt,
        metacognition_prompt=item.metacognition_prompt,
        marks=item.marks,
        difficulty=item.difficulty,
        calculator_policy=item.calculator_policy,
        notation_style=item.notation_style,
        hint_ladder=[HintRung(level=hint.level, title=hint.title, prompt=hint.prompt) for hint in item.hint_ladder],
    )


@router.get("/session/today", response_model=DailySessionPlanView)
def session_today(
    session_date: date | None = Query(default=None, alias="date"),
    student_id: str = Depends(require_student),
    bank: ItemBank = Depends(get_bank),
    store: LearningStore = Depends(get_store),
) -> DailySessionPlanView:
    session_date = session_date or date.today()
    attempts = store.list_attempts(student_id)
    plan = SessionEngine(bank).build_daily_plan(
        student_id=student_id,
        session_date=session_date,
        attempts=attempts,
    )
    return DailySessionPlanView(
        student_id=student_id,
        session_date=plan.session_date,
        tasks=[
            SessionTaskView(
                track=task.track.value,
                item_id=task.item_id,
                item_title=bank.get(task.item_id).title,
                reason=task.reason,
                locked=task.locked,
            )
            for task in plan.tasks
        ],
        notes=list(plan.notes),
    )


@router.get("/mastery", response_model=MasterySnapshotView)
def mastery(
    student_id: str = Depends(require_student),
    store: LearningStore = Depends(get_store),
    graph: dict = Depends(get_concept_graph),
) -> MasterySnapshotView:
    attempts = store.list_attempts(student_id)
    vectors = calculate_mastery_vectors(attempts)
    return MasterySnapshotView(
        student_id=student_id,
        vectors=vector_views(vectors, graph),
        generated_at=datetime.now(),
    )


@router.get("/retention/due", response_model=RetentionDueResponse)
def retention_due(
    as_of: date | None = None,
    student_id: str = Depends(require_student),
    bank: ItemBank = Depends(get_bank),
    store: LearningStore = Depends(get_store),
) -> RetentionDueResponse:
    as_of = as_of or date.today()
    attempts = store.list_attempts(student_id)
    due = due_retention_reviews(attempts, as_of=as_of, limit=5)
    return RetentionDueResponse(
        due=[
            RetentionDueView(
                item_id=item.item_id,
                item_title=bank.get(item.item_id).title,
                concept_ids=list(item.concept_ids),
                first_correct_date=item.first_correct_date,
                days_since=item.days_since,
                reason=item.reason,
            )
            for item in due
        ]
    )


@router.get("/weakness-report", response_model=WeaknessReportStudentView)
def weakness_report(
    window_days: int = 14,
    student_id: str = Depends(require_student),
    store: LearningStore = Depends(get_store),
    graph: dict = Depends(get_concept_graph),
) -> WeaknessReportStudentView:
    attempts = store.list_attempts(student_id)
    report = build_weakness_report(
        student_id=student_id,
        attempts=attempts,
        generated_at=datetime.now(),
        window_days=window_days,
    )
    vectors = calculate_mastery_vectors(attempts)
    return WeaknessReportStudentView(
        stuck_point_sentence=report.stuck_point_sentence,
        mastery_vectors=vector_views(vectors, graph),
    )


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
