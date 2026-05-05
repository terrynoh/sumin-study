from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends

from app.dependencies import get_store, require_parent
from app.schemas import ParentSummarySentRequest, ParentSummarySentView, ParentWeeklySummaryView
from backend.models import ParentSummary
from backend.persistence import LearningStore
from backend.weakness_report import build_weakness_report


router = APIRouter(prefix="/parent")


@router.get("/weekly-summary", response_model=ParentWeeklySummaryView)
def weekly_summary(
    as_of: date | None = None,
    student_id: str = Depends(require_parent),
    store: LearningStore = Depends(get_store),
) -> ParentWeeklySummaryView:
    week_start, week_end = _week_bounds(as_of or date.today())
    summary = _ensure_parent_summary(store, student_id, week_start, week_end)
    return _summary_view(summary)


@router.post("/weekly-summary/sent", response_model=ParentSummarySentView)
def mark_weekly_summary_sent(
    request: ParentSummarySentRequest | None = Body(default=None),
    as_of: date | None = None,
    student_id: str = Depends(require_parent),
    store: LearningStore = Depends(get_store),
) -> ParentSummarySentView:
    week_start, week_end = _week_bounds(as_of or date.today())
    _ensure_parent_summary(store, student_id, week_start, week_end)
    sent_at = request.sent_at if request and request.sent_at else datetime.now()
    store.mark_summary_sent(student_id, week_start, sent_at)
    summary = store.get_parent_summary(student_id, week_start)
    if summary is None:
        raise RuntimeError("Parent summary disappeared after marking sent.")
    return ParentSummarySentView(
        week_start=summary.week_start,
        week_end=summary.week_end,
        draft_status="sent",
        sent_at=summary.sent_at or sent_at,
    )


def _ensure_parent_summary(
    store: LearningStore,
    student_id: str,
    week_start: date,
    week_end: date,
) -> ParentSummary:
    generated_at = datetime.combine(week_end, datetime.max.time())
    report = build_weakness_report(
        student_id=student_id,
        attempts=store.list_attempts(student_id),
        generated_at=generated_at,
        window_days=7,
    )
    store.upsert_parent_summary(
        student_id,
        week_start,
        week_end,
        _summary_sections(report),
        created_at=datetime.now(),
    )
    summary = store.get_parent_summary(student_id, week_start)
    if summary is None:
        raise RuntimeError("Parent summary was not created.")
    return summary


def _summary_sections(report) -> dict[str, str]:
    if report.attempts_count == 0:
        improving = "Sumin is at the beginning of this week's practice pattern."
    elif report.correct_count == report.attempts_count:
        improving = "Sumin is showing a steady pattern in recent quadratics practice."
    else:
        improving = "Sumin is continuing to build fluency with quadratics through targeted practice."
    return {
        "improving": improving,
        "still_developing": _parent_safe_developing_sentence(report),
        "one_thing_that_would_help": report.support_action_parent,
    }


def _parent_safe_developing_sentence(report) -> str:
    if report.attempts_count == 0:
        return "A clearer learning pattern will take shape after a few more attempts."
    sentence = report.stuck_point_sentence
    if sentence == "There is not enough recent error data to identify a stable stuck point yet.":
        return "Sumin's next focus area is still taking shape."
    return sentence.replace("error", "pattern").replace("issue", "focus area")


def _summary_view(summary: ParentSummary) -> ParentWeeklySummaryView:
    return ParentWeeklySummaryView(
        week_start=summary.week_start,
        week_end=summary.week_end,
        improving=summary.improving,
        still_developing=summary.still_developing,
        one_thing_that_would_help=summary.one_thing_that_would_help,
        draft_status="sent" if summary.sent_at else "unsent",
        sent_at=summary.sent_at,
    )


def _week_bounds(day: date) -> tuple[date, date]:
    start = day - timedelta(days=day.weekday())
    return start, start + timedelta(days=6)
