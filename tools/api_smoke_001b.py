from __future__ import annotations

import os
import tempfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / ".tmp" / "api_smoke_001b.sqlite"
DB_PATH.parent.mkdir(exist_ok=True)
DB_PATH.unlink(missing_ok=True)
os.environ["SUMIN_STUDY_DB_PATH"] = str(DB_PATH)

from fastapi.testclient import TestClient

from app.main import app


def headers(student_id: str) -> dict[str, str]:
    return {"X-Role": "student", "X-Student-Id": student_id}


def main() -> None:
    with TestClient(app) as client:
        tests = [
            test_attempt_correct_first_try,
            test_attempt_incorrect_routes_to_repair,
            test_attempt_field_stripping_no_internal_leakage,
            test_repair_correct_returns_to_original,
            test_repair_incorrect_increases_depth_and_chains,
            test_repair_three_failures_escalates,
            test_repair_chain_avoids_revisit,
            test_attempt_track_repair_without_context_is_400,
            test_attempt_track_core_with_context_is_400,
            test_attempt_unknown_item_404,
            test_attempt_invalid_hint_level_422,
            test_attempt_repair_context_unknown_original_409,
            test_reflection_stored_returns_true,
            test_reflection_updates_articulation_mastery,
            test_reflection_empty_text_400,
            test_reflection_unknown_item_404,
        ]
        for test in tests:
            test(client)
            print(f"PASS {test.__name__}")


def post_q005_factor_signs(client: TestClient, student_id: str) -> dict:
    response = client.post(
        "/attempts",
        headers=headers(student_id),
        json={
            "item_id": "Q-005",
            "track": "core",
            "submitted_answer": "x = -3 or x = -5",
            "submitted_steps": ["x + 3 = 0"],
            "hint_level_used": 1,
            "selected_error_code": "Q005_FACTOR_SIGNS",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_attempt_correct_first_try(client: TestClient) -> None:
    response = client.post(
        "/attempts",
        headers=headers("attempt-correct"),
        json={
            "item_id": "Q-001",
            "track": "core",
            "submitted_answer": "(x + 3)(x + 2)",
            "submitted_steps": ["(x + 2)(x + 3)"],
            "hint_level_used": 0,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["attempt_id"] is not None
    assert data["correct"] is True
    assert data["next_track"] == "core"
    assert data["repair_context_after"] is None
    assert data["path_match_status"] in {"matched", "n/a"}
    assert data["mastery_vectors"]
    assert {vector["concept_id"] for vector in data["mastery_vectors"]}.issubset({"quad.factorise_monic"})


def test_attempt_incorrect_routes_to_repair(client: TestClient) -> None:
    data = post_q005_factor_signs(client, "attempt-incorrect")
    assert data["correct"] is False
    assert data["selected_error_code"] == "Q005_FACTOR_SIGNS"
    assert data["stuck_point"]["error_code"] == "Q005_FACTOR_SIGNS"
    assert data["stuck_point"]["matched"] is True
    assert data["next_track"] == "repair"
    assert data["next_item_id"].startswith("CR-")
    assert data["repair_context_after"]["depth"] == 0
    assert data["repair_context_after"]["original_item_id"] == "Q-005"


def test_attempt_field_stripping_no_internal_leakage(client: TestClient) -> None:
    data = post_q005_factor_signs(client, "attempt-no-leak")
    assert "confidence" not in data
    assert "confidence" not in data["stuck_point"]


def test_repair_correct_returns_to_original(client: TestClient) -> None:
    first = post_q005_factor_signs(client, "repair-correct")
    repair_item = first["next_item_id"]
    response = client.post(
        "/attempts",
        headers=headers("repair-correct"),
        json={
            "item_id": repair_item,
            "track": "repair",
            "submitted_answer": "both negative",
            "submitted_steps": ["both negative"],
            "repair_context": first["repair_context_after"],
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["correct"] is True
    assert data["repair_context_after"] is None
    assert data["next_item_id"] == "Q-005"
    assert data["next_track"] == "core"


def test_repair_incorrect_increases_depth_and_chains(client: TestClient) -> None:
    first = post_q005_factor_signs(client, "repair-depth")
    repair_item = first["next_item_id"]
    response = client.post(
        "/attempts",
        headers=headers("repair-depth"),
        json={
            "item_id": repair_item,
            "track": "repair",
            "submitted_answer": "both positive",
            "submitted_steps": ["both positive"],
            "repair_context": first["repair_context_after"],
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["repair_context_after"]["depth"] == 1
    assert data["repair_context_after"]["repair_chain"] == [repair_item]
    assert data["repair_context_after"]["escalated"] is False


def test_repair_three_failures_escalates(client: TestClient) -> None:
    first = post_q005_factor_signs(client, "repair-escalate")
    second = client.post(
        "/attempts",
        headers=headers("repair-escalate"),
        json={
            "item_id": first["next_item_id"],
            "track": "repair",
            "submitted_answer": "both positive",
            "submitted_steps": ["both positive"],
            "repair_context": first["repair_context_after"],
        },
    ).json()
    third = client.post(
        "/attempts",
        headers=headers("repair-escalate"),
        json={
            "item_id": second["next_item_id"],
            "track": "repair",
            "submitted_answer": "smaller number positive",
            "submitted_steps": ["smaller number positive"],
            "repair_context": second["repair_context_after"],
        },
    ).json()
    final = client.post(
        "/attempts",
        headers=headers("repair-escalate"),
        json={
            "item_id": first["next_item_id"],
            "track": "repair",
            "submitted_answer": "both positive",
            "submitted_steps": ["both positive"],
            "repair_context": third["repair_context_after"],
        },
    )
    assert final.status_code == 201, final.text
    data = final.json()
    assert data["repair_context_after"]["escalated"] is True
    assert data["next_item_id"] == "Q-005"
    assert data["next_track"] == "core"


def test_repair_chain_avoids_revisit(client: TestClient) -> None:
    first = post_q005_factor_signs(client, "repair-chain")
    first_repair = first["next_item_id"]
    response = client.post(
        "/attempts",
        headers=headers("repair-chain"),
        json={
            "item_id": first_repair,
            "track": "repair",
            "submitted_answer": "both positive",
            "submitted_steps": ["both positive"],
            "repair_context": first["repair_context_after"],
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["next_track"] == "repair"
    assert data["next_item_id"] != first_repair


def test_attempt_track_repair_without_context_is_400(client: TestClient) -> None:
    response = client.post(
        "/attempts",
        headers=headers("repair-no-context"),
        json={"item_id": "CR-003", "track": "repair", "submitted_answer": "both negative"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REPAIR_CONTEXT_MISSING"


def test_attempt_track_core_with_context_is_400(client: TestClient) -> None:
    response = client.post(
        "/attempts",
        headers=headers("core-with-context"),
        json={
            "item_id": "Q-001",
            "track": "core",
            "submitted_answer": "(x + 2)(x + 3)",
            "repair_context": {
                "original_item_id": "Q-005",
                "original_track": "core",
                "repair_chain": [],
                "depth": 0,
                "escalated": False,
            },
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "REPAIR_CONTEXT_UNEXPECTED"


def test_attempt_unknown_item_404(client: TestClient) -> None:
    response = client.post(
        "/attempts",
        headers=headers("unknown-item"),
        json={"item_id": "Q-999", "track": "core", "submitted_answer": "x"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


def test_attempt_invalid_hint_level_422(client: TestClient) -> None:
    response = client.post(
        "/attempts",
        headers=headers("bad-hint"),
        json={"item_id": "Q-001", "track": "core", "submitted_answer": "x", "hint_level_used": 5},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_attempt_repair_context_unknown_original_409(client: TestClient) -> None:
    response = client.post(
        "/attempts",
        headers=headers("stale-context"),
        json={
            "item_id": "CR-003",
            "track": "repair",
            "submitted_answer": "both negative",
            "repair_context": {
                "original_item_id": "Q-999",
                "original_track": "core",
                "repair_chain": [],
                "depth": 0,
                "escalated": False,
            },
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ORIGINAL_ITEM_NOT_FOUND"


def test_reflection_stored_returns_true(client: TestClient) -> None:
    response = client.post(
        "/reflections",
        headers=headers("reflection-ok"),
        json={
            "item_id": "Q-001",
            "reflection_text": "I checked the product and sum separately.",
            "articulation_ok": True,
        },
    )
    assert response.status_code == 201
    assert response.json() == {"stored": True}
    reflections = client.app.state.store.list_reflections("reflection-ok")
    assert len(reflections) == 1
    assert reflections[0].reflection_text == "I checked the product and sum separately."


def test_reflection_updates_articulation_mastery(client: TestClient) -> None:
    student_id = "reflection-mastery"
    response = client.post(
        "/attempts",
        headers=headers(student_id),
        json={
            "item_id": "Q-001",
            "track": "core",
            "submitted_answer": "(x + 3)(x + 2)",
            "submitted_steps": ["(x + 3)(x + 2)"],
            "hint_level_used": 0,
        },
    )
    assert response.status_code == 201
    response = client.post(
        "/reflections",
        headers=headers(student_id),
        json={
            "item_id": "Q-001",
            "reflection_text": "The two factors multiply to 6 and add to 5.",
            "articulation_ok": True,
        },
    )
    assert response.status_code == 201
    response = client.get("/mastery", headers=headers(student_id))
    assert response.status_code == 200
    vector = response.json()["vectors"][0]
    assert vector["concept_id"] == "quad.factorise_monic"
    assert vector["articulation"] == "ready"


def test_reflection_empty_text_400(client: TestClient) -> None:
    response = client.post(
        "/reflections",
        headers=headers("reflection-empty"),
        json={"item_id": "Q-001", "reflection_text": "   "},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_REFLECTION"


def test_reflection_unknown_item_404(client: TestClient) -> None:
    response = client.post(
        "/reflections",
        headers=headers("reflection-unknown"),
        json={"item_id": "Q-999", "reflection_text": "Something."},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ITEM_NOT_FOUND"


if __name__ == "__main__":
    try:
        main()
    finally:
        DB_PATH.unlink(missing_ok=True)
