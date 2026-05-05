from __future__ import annotations

from datetime import date, datetime

from backend.item_bank import ItemBank
from backend.mastery import calculate_mastery_vectors
from backend.models import AttemptRecord, DimensionState, Track
from backend.persistence import LearningStore
from backend.session_engine import SessionEngine


def test_daily_plan_starts_with_three_core_items() -> None:
    bank = ItemBank.from_directory("content/quadratics/items/extended")
    plan = SessionEngine(bank).build_daily_plan(
        student_id="sumin",
        session_date=date(2026, 5, 3),
        attempts=[],
    )

    assert [task.item_id for task in plan.core] == ["Q-001", "Q-002", "Q-003"]
    assert plan.explore and plan.explore[0].locked is True


def test_mastery_vector_uses_five_dimensions() -> None:
    attempts = [
        AttemptRecord("Q-001", ("quad.factorise_monic",), Track.CORE, True, 0, datetime(2026, 5, 1)),
        AttemptRecord("Q-002", ("quad.factorise_monic",), Track.CORE, True, 1, datetime(2026, 5, 2), transfer_variation_of="Q-001"),
        AttemptRecord("Q-003", ("quad.factorise_monic",), Track.CORE, True, 1, datetime(2026, 5, 3), articulation_ok=True),
        AttemptRecord("Q-004", ("quad.factorise_monic",), Track.REVIEW, True, 0, datetime(2026, 5, 5)),
    ]

    vector = calculate_mastery_vectors(attempts)["quad.factorise_monic"]

    assert vector.accuracy == DimensionState.READY
    assert vector.hint_independence == DimensionState.READY
    assert vector.retention == DimensionState.READY
    assert vector.transfer == DimensionState.READY
    assert vector.articulation == DimensionState.READY
    assert vector.mastered is True


def test_failed_core_routes_to_repair() -> None:
    bank = ItemBank.from_directory("content/quadratics/items/extended")
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


def test_sqlite_store_round_trip(tmp_path) -> None:
    store = LearningStore(tmp_path / "study.sqlite")
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

    assert store.list_attempts("sumin") == [attempt]

