from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEMP_ROOT = ROOT / ".tmp"
TEMP_ROOT.mkdir(exist_ok=True)


def temp_db_path(name: str) -> Path:
    path = TEMP_ROOT / name
    path.unlink(missing_ok=True)
    return path

from backend.item_bank import ItemBank
from backend.item_bank_holder import ItemBankHolder
from backend.answer_checker import check_answer
from backend.attempt_service import AttemptService, AttemptSubmission
from backend.mastery import calculate_mastery_vectors
from backend.models import AttemptRecord, DimensionState, Track
from backend.models import RepairContext
from backend.persistence import LearningStore
from backend.retention import due_retention_reviews
from backend.session_engine import SessionEngine
from backend.step_checker import StepStatus, check_submitted_steps, first_error_code_from_steps
from backend.weakness_report import build_weakness_report


def check_daily_plan() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")
    plan = SessionEngine(bank).build_daily_plan(
        student_id="sumin",
        session_date=date(2026, 5, 3),
        attempts=[],
    )
    assert [task.item_id for task in plan.core] == ["Q-001", "Q-002", "Q-003"]
    assert plan.explore and plan.explore[0].locked is True


def check_item_bank_loads_extended_and_core_repair() -> None:
    bank = ItemBank.from_directory_tree(ROOT / "content" / "quadratics" / "items")
    assert len(bank.by_tier("extended")) == 20
    assert len(bank.by_tier("core_repair")) == 25
    assert bank.core_repair_items_for("num.negative_numbers")
    plan = SessionEngine(bank).build_daily_plan(
        student_id="sumin",
        session_date=date(2026, 5, 3),
        attempts=[],
    )
    assert plan.core
    assert all(bank.get(task.item_id).tier == "extended" for task in plan.core)


def check_year10_core_path_excludes_stretch_items() -> None:
    bank = ItemBank.from_directory_tree(ROOT / "content" / "quadratics" / "items")
    attempts = [
        AttemptRecord(
            item.id,
            tuple(item.concept_ids),
            Track.CORE,
            True,
            0,
            datetime(2026, 5, 1),
        )
        for item in bank.by_tier("extended")
        if item.year10_sequence_band == "core_target"
    ]
    plan = SessionEngine(bank).build_daily_plan(
        student_id="sumin",
        session_date=date(2026, 5, 3),
        attempts=attempts,
    )
    assert plan.core
    assert all(bank.get(task.item_id).year10_sequence_band != "stretch" for task in plan.core)
    assert [task.item_id for task in plan.core] == ["Q-015", "Q-016", "Q-017"]


def check_mastery_vector() -> None:
    attempts = [
        AttemptRecord("Q-001", ("quad.factorise_monic",), Track.CORE, True, 0, datetime(2026, 5, 1)),
        AttemptRecord(
            "Q-002",
            ("quad.factorise_monic",),
            Track.CORE,
            True,
            1,
            datetime(2026, 5, 2),
            transfer_variation_of="Q-001",
        ),
        AttemptRecord(
            "Q-003",
            ("quad.factorise_monic",),
            Track.CORE,
            True,
            1,
            datetime(2026, 5, 3),
            articulation_ok=True,
        ),
        AttemptRecord("Q-004", ("quad.factorise_monic",), Track.REVIEW, True, 0, datetime(2026, 5, 5)),
    ]
    vector = calculate_mastery_vectors(attempts)["quad.factorise_monic"]
    assert vector.accuracy == DimensionState.READY
    assert vector.hint_independence == DimensionState.READY
    assert vector.retention == DimensionState.READY
    assert vector.transfer == DimensionState.READY
    assert vector.articulation == DimensionState.READY
    assert vector.mastered is True


def check_repair_routing() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")
    engine = SessionEngine(bank)
    attempt = AttemptRecord(
        item_id="Q-001",
        concept_ids=("quad.factorise_monic",),
        track=Track.CORE,
        correct=False,
        hint_level_used=3,
        attempted_at=datetime(2026, 5, 3, 18, 0, 0),
        error_category="strategy_selection_error",
        repair_node_ids=("quad.factorise_monic",),
    )
    assert engine.route_after_attempt(attempt) == Track.REPAIR


def check_repair_routing_prefers_core_repair() -> None:
    bank = ItemBank.from_directory_tree(ROOT / "content" / "quadratics" / "items", active_only=False)
    attempts = [
        AttemptRecord(
            item_id="Q-005",
            concept_ids=("quad.solve_by_factorising",),
            track=Track.CORE,
            correct=False,
            hint_level_used=2,
            attempted_at=datetime(2026, 5, 3, 18, 0, 0),
            error_category="sign_error",
            repair_node_ids=("num.negative_numbers",),
        )
    ]
    plan = SessionEngine(bank).build_daily_plan(
        student_id="sumin",
        session_date=date(2026, 5, 3),
        attempts=attempts,
    )
    assert plan.repair
    assert bank.get(plan.repair[0].item_id).tier == "core_repair"


def check_sqlite_round_trip() -> None:
    store = LearningStore(temp_db_path("phase2_sqlite_round_trip.sqlite"))
    attempt = AttemptRecord(
        item_id="Q-005",
        concept_ids=("quad.solve_by_factorising", "quad.factorise_monic"),
        track=Track.CORE,
        correct=False,
        hint_level_used=4,
        attempted_at=datetime(2026, 5, 3, 18, 15, 0),
        error_category="checking_finalization_error",
        repair_node_ids=("exam.command_solve", "quad.solve_by_factorising"),
    )
    store.add_attempt("sumin", attempt)
    listed = store.list_attempts("sumin")
    assert len(listed) == 1
    assert listed[0].id is not None
    assert listed[0].item_id == attempt.item_id
    assert listed[0].repair_node_ids == attempt.repair_node_ids


def check_attempt_id_round_trip() -> None:
    store = LearningStore(temp_db_path("phase2_attempt_id.sqlite"))
    store.add_attempt(
        "sumin",
        AttemptRecord(
            item_id="Q-001",
            concept_ids=("quad.factorise_monic",),
            track=Track.CORE,
            correct=True,
            hint_level_used=0,
            attempted_at=datetime(2026, 5, 3, 18, 1, 0),
            path_match_status="matched",
        ),
    )
    attempt = store.list_attempts("sumin")[0]
    assert attempt.id is not None
    assert attempt.path_match_status == "matched"


def check_path_match_status_unmatched() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")
    store = LearningStore(temp_db_path("phase2_unmatched.sqlite"))
    service = AttemptService(bank, store)
    outcome = service.submit(
        student_id="sumin",
        submission=AttemptSubmission(
            item_id="Q-001",
            track=Track.CORE,
            submitted_answer="(x + 3)(x + 2)",
            submitted_steps=("I used a different mental route.",),
        ),
        attempted_at=datetime(2026, 5, 3, 18, 2, 0),
    )
    assert outcome.check.correct is True
    listed = store.list_attempts("sumin")
    assert listed[0].path_match_status == "unmatched"
    unmatched = store.list_unmatched_paths("sumin")
    assert len(unmatched) == 1
    assert unmatched[0].item_id == "Q-001"
    unmatched_steps = store.list_unmatched_path_steps("sumin")
    assert len(unmatched_steps) == 1
    assert unmatched_steps[0].attempt_id == unmatched[0].id
    assert unmatched_steps[0].submitted_steps == ("I used a different mental route.",)


def check_reflection_round_trip() -> None:
    store = LearningStore(temp_db_path("phase2_reflection.sqlite"))
    submitted_at = datetime(2026, 5, 3, 18, 3, 0)
    store.add_attempt(
        "sumin",
        AttemptRecord(
            item_id="Q-001",
            concept_ids=("quad.factorise_monic",),
            track=Track.CORE,
            correct=True,
            hint_level_used=0,
            attempted_at=datetime(2026, 5, 3, 18, 2, 0),
        ),
    )
    store.add_reflection(
        "sumin",
        "Q-001",
        "I checked the product and sum separately.",
        True,
        submitted_at,
    )
    assert store.update_latest_attempt_articulation("sumin", "Q-001", True) is True
    reflections = store.list_reflections("sumin")
    assert len(reflections) == 1
    assert reflections[0].id is not None
    assert reflections[0].reflection_text == "I checked the product and sum separately."
    assert reflections[0].articulation_ok is True
    assert reflections[0].submitted_at == submitted_at
    assert store.list_attempts("sumin")[0].articulation_ok is True


def check_parent_summary_upsert() -> None:
    store = LearningStore(temp_db_path("phase2_parent_summary.sqlite"))
    week_start = date(2026, 4, 27)
    week_end = date(2026, 5, 3)
    store.upsert_parent_summary(
        "sumin",
        week_start,
        week_end,
        {
            "improving": "She is checking factor pairs more consistently.",
            "still_developing": "Negative signs still need slow checking.",
            "one_thing_that_would_help": "Spend five minutes on sign pairs.",
        },
        created_at=datetime(2026, 5, 3, 18, 4, 0),
    )
    summary = store.get_parent_summary("sumin", week_start)
    assert summary is not None
    assert summary.id is not None
    assert summary.sent_at is None
    store.upsert_parent_summary(
        "sumin",
        week_start,
        week_end,
        {
            "improving": "Updated improving text.",
            "still_developing": "Updated developing text.",
            "one_thing_that_would_help": "Updated support action.",
        },
    )
    updated = store.get_parent_summary("sumin", week_start)
    assert updated is not None
    assert updated.improving == "Updated improving text."
    sent_at = datetime(2026, 5, 3, 18, 5, 0)
    store.mark_summary_sent("sumin", week_start, sent_at)
    sent = store.get_parent_summary("sumin", week_start)
    assert sent is not None
    assert sent.sent_at == sent_at


def check_item_bank_holder_swap() -> None:
    root = ROOT / "content" / "quadratics" / "items"
    initial = ItemBank.from_directory_tree(root)
    holder = ItemBankHolder(initial)
    before = holder.current()
    after = holder.reload(root)
    assert before is not after
    assert holder.current() is after
    assert len(after.by_tier("core_repair")) == 25


def check_answer_checker_and_attempt_flow() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")

    q1 = bank.get("Q-001")
    assert check_answer(q1, "(x + 3)(x + 2)").correct is True

    q5 = bank.get("Q-005")
    check = check_answer(q5, "(x - 3)(x - 5)")
    assert check.correct is False
    assert check.selected_error_code == "Q005_STOPS_AT_FACTORS"

    service = AttemptService(bank, LearningStore(temp_db_path("phase2_attempt_flow.sqlite")))
    outcome = service.submit(
        student_id="sumin",
        submission=AttemptSubmission(
            item_id="Q-005",
            track=Track.CORE,
            submitted_answer="(x - 3)(x - 5)",
            hint_level_used=2,
        ),
        attempted_at=datetime(2026, 5, 3, 18, 30, 0),
    )
    assert outcome.check.correct is False
    assert outcome.recorded_attempt.id is not None
    assert outcome.stuck_point is not None
    assert outcome.stuck_point.diagnostic_target == "solve_after_factorising"
    assert outcome.next_track == Track.REPAIR


def check_repair_context_returns_to_original() -> None:
    bank = ItemBank.from_directory_tree(ROOT / "content" / "quadratics" / "items", active_only=False)
    service = AttemptService(bank, LearningStore(temp_db_path("phase2_repair_return.sqlite")))
    context = RepairContext(original_item_id="Q-005", original_track=Track.CORE, repair_chain=("CR-003",), depth=1)
    outcome = service.submit(
        student_id="sumin",
        submission=AttemptSubmission(
            item_id="CR-003",
            track=Track.REPAIR,
            submitted_answer="both negative",
            repair_context=context,
        ),
        attempted_at=datetime(2026, 5, 3, 18, 40, 0),
    )
    assert outcome.repair_context_after is None
    assert service.next_item_after(outcome) == ("Q-005", Track.CORE)


def check_repair_context_max_depth_3_escalation() -> None:
    bank = ItemBank.from_directory_tree(ROOT / "content" / "quadratics" / "items", active_only=False)
    service = AttemptService(bank, LearningStore(temp_db_path("phase2_repair_escalation.sqlite")))
    context = RepairContext(
        original_item_id="Q-005",
        original_track=Track.CORE,
        repair_chain=("CR-003", "CR-004"),
        depth=2,
    )
    outcome = service.submit(
        student_id="sumin",
        submission=AttemptSubmission(
            item_id="CR-003",
            track=Track.REPAIR,
            submitted_answer="not sure",
            repair_context=context,
        ),
        attempted_at=datetime(2026, 5, 3, 18, 45, 0),
    )
    assert outcome.repair_context_after is not None
    assert outcome.repair_context_after.escalated is True
    assert service.next_item_after(outcome) == ("Q-005", Track.CORE)


def check_retention_scheduler_and_weakness_report() -> None:
    attempts = [
        AttemptRecord("Q-001", ("quad.factorise_monic",), Track.CORE, True, 0, datetime(2026, 5, 1)),
        AttemptRecord(
            "Q-005",
            ("quad.solve_by_factorising",),
            Track.CORE,
            False,
            2,
            datetime(2026, 5, 3),
            error_category="checking_finalization_error",
            diagnostic_target="solve_after_factorising",
            diagnostic_sentence="You factorised correctly, but the command word is 'Solve'.",
            repair_node_ids=("exam.command_solve", "quad.solve_by_factorising"),
        ),
    ]

    due = due_retention_reviews(attempts, as_of=date(2026, 5, 4))
    assert len(due) == 1
    assert due[0].item_id == "Q-001"
    assert "3 days" in due[0].reason

    report = build_weakness_report(
        student_id="sumin",
        attempts=attempts,
        generated_at=datetime(2026, 5, 4),
    )
    assert report.top_error_category == "checking_finalization_error"
    assert report.top_repair_node_id == "exam.command_solve"
    assert "factorised correctly" in report.stuck_point_sentence
    assert "repair_node=exam.command_solve" in report.support_action_operator
    assert "final line check" in report.support_action_parent.lower()


def check_task_order_core_first() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")
    attempts = [
        AttemptRecord("Q-001", ("quad.factorise_monic",), Track.CORE, True, 0, datetime(2026, 5, 1)),
    ]
    plan = SessionEngine(bank).build_daily_plan(
        student_id="sumin",
        session_date=date(2026, 5, 4),
        attempts=attempts,
    )
    assert plan.core
    assert plan.review
    assert plan.tasks[0].track == Track.CORE


def check_step_level_checker() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")
    item = bank.get("Q-005")
    checks = check_submitted_steps(item, ("(x - 3)(x - 5)",))
    assert checks[0].status == StepStatus.LIKELY_ERROR
    assert checks[0].selected_error_code == "Q005_STOPS_AT_FACTORS"
    assert first_error_code_from_steps(checks) == "Q005_STOPS_AT_FACTORS"


def main() -> None:
    checks = [
        check_daily_plan,
        check_item_bank_loads_extended_and_core_repair,
        check_year10_core_path_excludes_stretch_items,
        check_mastery_vector,
        check_repair_routing,
        check_repair_routing_prefers_core_repair,
        check_sqlite_round_trip,
        check_attempt_id_round_trip,
        check_path_match_status_unmatched,
        check_reflection_round_trip,
        check_parent_summary_upsert,
        check_item_bank_holder_swap,
        check_answer_checker_and_attempt_flow,
        check_repair_context_returns_to_original,
        check_repair_context_max_depth_3_escalation,
        check_retention_scheduler_and_weakness_report,
        check_task_order_core_first,
        check_step_level_checker,
    ]
    for check in checks:
        check()
        print(f"PASS {check.__name__}")


if __name__ == "__main__":
    main()
