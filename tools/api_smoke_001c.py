from __future__ import annotations

import os
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / ".tmp" / "api_smoke_001c.sqlite"
DB_PATH.parent.mkdir(exist_ok=True)
DB_PATH.unlink(missing_ok=True)
os.environ["SUMIN_STUDY_DB_PATH"] = str(DB_PATH)

from fastapi.testclient import TestClient

from app.main import app


OP_HEADERS = {"X-Role": "operator", "X-Student-Id": "operator-demo"}
STUDENT_HEADERS = {"X-Role": "student", "X-Student-Id": "operator-demo"}
PARENT_HEADERS = {"X-Role": "parent", "X-Student-Id": "operator-demo"}


def main() -> None:
    with TestClient(app) as client:
        tests = [
            test_operator_endpoints_require_operator_role,
            test_operator_endpoints_missing_role_422,
            test_operator_role_passes,
            test_operator_items_returns_full_bank_with_counts,
            test_operator_items_gates_all_ok_for_active_pool,
            test_operator_items_aggregates_attempt_counts,
            test_operator_item_returns_full_schema,
            test_operator_item_404_for_unknown,
            test_operator_attempts_returns_history,
            test_operator_attempts_strips_verbatim_fields,
            test_operator_attempts_since_filter,
            test_operator_weakness_report_includes_operator_fields,
            test_operator_weakness_report_excludes_student_view_only,
            test_operator_unmatched_paths_returns_only_unmatched,
            test_operator_unmatched_paths_includes_submitted_steps,
            test_operator_reload_returns_new_counts,
            test_operator_reload_swaps_holder_instance,
        ]
        for test in tests:
            test(client)
            print(f"PASS {test.__name__}")


def submit_attempt(client: TestClient, student_id: str, *, item_id="Q-001", answer="(x + 2)(x + 3)", steps=None) -> dict:
    response = client.post(
        "/attempts",
        headers={"X-Role": "student", "X-Student-Id": student_id},
        json={
            "item_id": item_id,
            "track": "core",
            "submitted_answer": answer,
            "submitted_steps": steps if steps is not None else ["(x + 2)(x + 3)"],
            "hint_level_used": 1,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_operator_endpoints_require_operator_role(client: TestClient) -> None:
    for bad_headers in (STUDENT_HEADERS, PARENT_HEADERS):
        response = client.get("/operator/items", headers=bad_headers)
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "ROLE_MISMATCH"


def test_operator_endpoints_missing_role_422(client: TestClient) -> None:
    response = client.get("/operator/items")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_operator_role_passes(client: TestClient) -> None:
    response = client.get("/operator/items", headers=OP_HEADERS)
    assert response.status_code == 200


def test_operator_items_returns_full_bank_with_counts(client: TestClient) -> None:
    response = client.get("/operator/items", headers=OP_HEADERS)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 45
    assert sum(1 for item in items if item["tier"] == "extended") == 20
    assert sum(1 for item in items if item["tier"] == "core_repair") == 25


def test_operator_items_gates_all_ok_for_active_pool(client: TestClient) -> None:
    response = client.get("/operator/items", headers=OP_HEADERS)
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert set(item["gates"].values()) == {"ok"}


def test_operator_items_aggregates_attempt_counts(client: TestClient) -> None:
    submit_attempt(client, "operator-aggregate")
    response = client.get("/operator/items", headers={"X-Role": "operator", "X-Student-Id": "operator-aggregate"})
    assert response.status_code == 200
    q1 = next(item for item in response.json()["items"] if item["id"] == "Q-001")
    assert q1["attempt_count"] == 1
    assert q1["correct_ratio"] == 1.0
    assert q1["avg_hint_level"] == 1.0


def test_operator_item_returns_full_schema(client: TestClient) -> None:
    response = client.get("/operator/items/Q-001", headers=OP_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "expected_answer" in data
    assert "expected_solution_steps" in data
    assert "error_category_mapping" in data
    assert "source_reference" in data


def test_operator_item_404_for_unknown(client: TestClient) -> None:
    response = client.get("/operator/items/Q-999", headers=OP_HEADERS)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


def test_operator_attempts_returns_history(client: TestClient) -> None:
    submit_attempt(client, "operator-history")
    response = client.get("/operator/attempts", headers={"X-Role": "operator", "X-Student-Id": "operator-history"})
    assert response.status_code == 200
    attempts = response.json()["attempts"]
    assert len(attempts) == 1
    assert attempts[0]["item_id"] == "Q-001"


def test_operator_attempts_strips_verbatim_fields(client: TestClient) -> None:
    submit_attempt(client, "operator-strip")
    response = client.get("/operator/attempts", headers={"X-Role": "operator", "X-Student-Id": "operator-strip"})
    data = response.json()["attempts"][0]
    forbidden = {"submitted_answer", "submitted_steps", "articulation_ok", "reflection_text"}
    assert not (forbidden & set(data))


def test_operator_attempts_since_filter(client: TestClient) -> None:
    submit_attempt(client, "operator-since")
    response = client.get(
        "/operator/attempts?since=2099-01-01",
        headers={"X-Role": "operator", "X-Student-Id": "operator-since"},
    )
    assert response.status_code == 200
    assert response.json()["attempts"] == []


def test_operator_weakness_report_includes_operator_fields(client: TestClient) -> None:
    client.post(
        "/attempts",
        headers={"X-Role": "student", "X-Student-Id": "operator-weakness"},
        json={
            "item_id": "Q-005",
            "track": "core",
            "submitted_answer": "x = -3 or x = -5",
            "submitted_steps": ["x + 3 = 0"],
            "selected_error_code": "Q005_FACTOR_SIGNS",
        },
    )
    response = client.get(
        "/operator/weakness-report",
        headers={"X-Role": "operator", "X-Student-Id": "operator-weakness"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "support_action_operator" in data
    assert "top_repair_node_id" in data
    assert "attempts_count" in data


def test_operator_weakness_report_excludes_student_view_only(client: TestClient) -> None:
    response = client.get("/operator/weakness-report", headers=OP_HEADERS)
    assert response.status_code == 200
    assert "mastery_vectors" not in response.json()


def test_operator_unmatched_paths_returns_only_unmatched(client: TestClient) -> None:
    submit_attempt(client, "operator-unmatched", steps=["I used a different mental route."])
    submit_attempt(client, "operator-unmatched", item_id="Q-002", answer="(x - 1)(x - 4)", steps=["(x - 1)(x - 4)"])
    response = client.get(
        "/operator/unmatched-paths",
        headers={"X-Role": "operator", "X-Student-Id": "operator-unmatched"},
    )
    assert response.status_code == 200
    unmatched = response.json()["unmatched"]
    assert len(unmatched) == 1
    assert unmatched[0]["item_id"] == "Q-001"


def test_operator_unmatched_paths_includes_submitted_steps(client: TestClient) -> None:
    submit_attempt(client, "operator-unmatched-steps", steps=["I used a different mental route."])
    response = client.get(
        "/operator/unmatched-paths",
        headers={"X-Role": "operator", "X-Student-Id": "operator-unmatched-steps"},
    )
    data = response.json()["unmatched"][0]
    assert data["submitted_steps"] == ["I used a different mental route."]
    assert "submitted_answer" not in data


def test_operator_reload_returns_new_counts(client: TestClient) -> None:
    response = client.post("/operator/item-bank/reload", headers=OP_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["item_bank"]["extended"] == 20
    assert data["item_bank"]["core_repair"] == 25
    assert "reloaded_at" in data


def test_operator_reload_swaps_holder_instance(client: TestClient) -> None:
    before = client.app.state.bank_holder.current()
    response = client.post("/operator/item-bank/reload", headers=OP_HEADERS)
    assert response.status_code == 200
    after = client.app.state.bank_holder.current()
    assert before is not after


if __name__ == "__main__":
    try:
        main()
    finally:
        DB_PATH.unlink(missing_ok=True)
