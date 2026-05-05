from __future__ import annotations

import os
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / ".tmp" / "api_smoke_001a.sqlite"
DB_PATH.parent.mkdir(exist_ok=True)
DB_PATH.unlink(missing_ok=True)
os.environ["SUMIN_STUDY_DB_PATH"] = str(DB_PATH)

from fastapi.testclient import TestClient

from app.main import app
from backend.item_bank import ItemBank
from backend.item_bank_holder import ItemBankHolder


STUDENT_HEADERS = {"X-Role": "student", "X-Student-Id": "sumin"}
FORBIDDEN_ITEM_FIELDS = {
    "expected_answer",
    "expected_solution_steps",
    "error_category_mapping",
    "accepted_alternative_paths",
    "mark_scheme_notes",
    "examiner_report_notes",
    "source_reference",
    "concept_ids",
    "prerequisite_ids",
    "exam_literacy_ids",
    "transfer_variation_of",
    "status",
}


def main() -> None:
    with TestClient(app) as client:
        tests = [
            test_health_returns_bank_counts,
            test_concept_graph_returns_schema_version,
            test_item_for_student_strips_solution_fields,
            test_item_404_for_unknown,
            test_item_404_for_draft_status,
            test_session_today_orders_core_first,
            test_session_today_with_explore_locked,
            test_mastery_returns_only_attempted_concepts,
            test_retention_due_returns_zero_for_fresh_student,
            test_weakness_report_student_variant_excludes_operator_fields,
            test_role_mismatch_returns_403,
            test_missing_x_role_returns_validation_error,
        ]
        for test in tests:
            test(client)
            print(f"PASS {test.__name__}")


def test_health_returns_bank_counts(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["item_bank"]["extended"] == 20
    assert data["item_bank"]["core_repair"] == 25
    assert "loaded_at" in data["item_bank"]
    assert data["db_path"].endswith(".sqlite")


def test_concept_graph_returns_schema_version(client: TestClient) -> None:
    response = client.get("/concept-graph")
    assert response.status_code == 200
    assert response.json()["schema_version"] == "0.1"


def test_item_for_student_strips_solution_fields(client: TestClient) -> None:
    response = client.get("/items/Q-001", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "Q-001"
    assert data["hint_ladder"]
    assert not (FORBIDDEN_ITEM_FIELDS & set(data))


def test_item_404_for_unknown(client: TestClient) -> None:
    response = client.get("/items/Q-999", headers=STUDENT_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


def test_item_404_for_draft_status(client: TestClient) -> None:
    active_bank = client.app.state.bank_holder.current()
    draft = active_bank.get("Q-001").model_copy(update={"id": "DRAFT-001", "status": "draft"})
    original_holder = client.app.state.bank_holder
    client.app.state.bank_holder = ItemBankHolder(ItemBank(active_bank.all() + [draft]))
    try:
        response = client.get("/items/DRAFT-001", headers=STUDENT_HEADERS)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"
    finally:
        client.app.state.bank_holder = original_holder


def test_session_today_orders_core_first(client: TestClient) -> None:
    response = client.get("/session/today?date=2026-05-03", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    tasks = response.json()["tasks"]
    assert tasks
    assert tasks[0]["track"] == "core"


def test_session_today_with_explore_locked(client: TestClient) -> None:
    response = client.get("/session/today?date=2026-05-03", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    explore = [task for task in response.json()["tasks"] if task["track"] == "explore"]
    assert explore
    assert explore[0]["locked"] is True


def test_mastery_returns_only_attempted_concepts(client: TestClient) -> None:
    response = client.get("/mastery", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    assert response.json()["vectors"] == []


def test_retention_due_returns_zero_for_fresh_student(client: TestClient) -> None:
    response = client.get("/retention/due?as_of=2026-05-03", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    assert response.json()["due"] == []


def test_weakness_report_student_variant_excludes_operator_fields(client: TestClient) -> None:
    response = client.get("/weakness-report", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    forbidden = {"support_action_operator", "support_action_parent", "top_repair_node_id", "attempts_count", "correct_count"}
    assert not (forbidden & set(data))
    assert "stuck_point_sentence" in data
    assert "mastery_vectors" in data


def test_role_mismatch_returns_403(client: TestClient) -> None:
    response = client.get("/session/today", headers={"X-Role": "operator"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ROLE_MISMATCH"


def test_missing_x_role_returns_validation_error(client: TestClient) -> None:
    response = client.get("/session/today")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


if __name__ == "__main__":
    try:
        main()
    finally:
        DB_PATH.unlink(missing_ok=True)
