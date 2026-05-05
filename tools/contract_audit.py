from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DB_PATH = ROOT / ".tmp" / "contract_audit.sqlite"
DB_PATH.parent.mkdir(exist_ok=True)
DB_PATH.unlink(missing_ok=True)
os.environ["SUMIN_STUDY_DB_PATH"] = str(DB_PATH)

from fastapi.testclient import TestClient

from app.main import app


STUDENT_ID = "contract-audit"
STUDENT_HEADERS = {"X-Role": "student", "X-Student-Id": STUDENT_ID}
OPERATOR_HEADERS = {"X-Role": "operator", "X-Student-Id": STUDENT_ID}
PARENT_HEADERS = {"X-Role": "parent", "X-Student-Id": STUDENT_ID}


def main() -> None:
    with TestClient(app) as client:
        checks = [
            check_route_surface,
            check_role_boundaries,
            check_student_item_stripping,
            check_operator_attempt_privacy,
            check_unmatched_path_exception,
            check_reflection_updates_articulation,
            check_parent_endpoint_privacy,
        ]
        for check in checks:
            check(client)
            print(f"PASS {check.__name__}")


def check_route_surface(client: TestClient) -> None:
    paths = {route.path for route in client.app.routes if hasattr(route, "methods")}
    expected = {
        "/health",
        "/concept-graph",
        "/items/{item_id}",
        "/session/today",
        "/mastery",
        "/retention/due",
        "/weakness-report",
        "/attempts",
        "/reflections",
        "/operator/items",
        "/operator/items/{item_id}",
        "/operator/attempts",
        "/operator/weakness-report",
        "/operator/unmatched-paths",
        "/operator/item-bank/reload",
        "/parent/weekly-summary",
        "/parent/weekly-summary/sent",
    }
    missing = expected - paths
    assert not missing, f"missing routes: {sorted(missing)}"


def check_role_boundaries(client: TestClient) -> None:
    assert client.get("/operator/items", headers=STUDENT_HEADERS).status_code == 403
    assert client.get("/session/today", headers=OPERATOR_HEADERS).status_code == 403


def check_student_item_stripping(client: TestClient) -> None:
    response = client.get("/items/Q-001", headers=STUDENT_HEADERS)
    assert response.status_code == 200
    forbidden = {
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
    assert not (forbidden & set(response.json()))


def check_operator_attempt_privacy(client: TestClient) -> None:
    _submit_matched_attempt(client, student_id="operator-privacy")
    response = client.get("/operator/attempts", headers={"X-Role": "operator", "X-Student-Id": "operator-privacy"})
    assert response.status_code == 200
    attempt = response.json()["attempts"][0]
    forbidden = {"submitted_answer", "submitted_steps", "articulation_ok", "reflection_text"}
    assert not (forbidden & set(attempt))


def check_unmatched_path_exception(client: TestClient) -> None:
    student_id = "unmatched-exception"
    _submit_unmatched_attempt(client, student_id=student_id)
    response = client.get("/operator/unmatched-paths", headers={"X-Role": "operator", "X-Student-Id": student_id})
    assert response.status_code == 200
    row = response.json()["unmatched"][0]
    assert row["submitted_steps"] == ["I used a different mental route."]
    assert "submitted_answer" not in row


def check_reflection_updates_articulation(client: TestClient) -> None:
    student_id = "reflection-contract"
    _submit_matched_attempt(client, student_id=student_id)
    response = client.post(
        "/reflections",
        headers={"X-Role": "student", "X-Student-Id": student_id},
        json={
            "item_id": "Q-001",
            "reflection_text": "The factors multiply to 6 and add to 5.",
            "articulation_ok": True,
        },
    )
    assert response.status_code == 201
    response = client.get("/mastery", headers={"X-Role": "student", "X-Student-Id": student_id})
    assert response.status_code == 200
    vectors = response.json()["vectors"]
    assert vectors
    assert vectors[0]["articulation"] == "ready"


def check_parent_endpoint_privacy(client: TestClient) -> None:
    response = client.get("/parent/weekly-summary?as_of=2026-05-03", headers=PARENT_HEADERS)
    assert response.status_code == 200
    data = response.json()
    allowed = {
        "week_start",
        "week_end",
        "improving",
        "still_developing",
        "one_thing_that_would_help",
        "draft_status",
        "sent_at",
    }
    forbidden = set(data) - allowed
    assert not forbidden, f"unexpected parent fields: {sorted(forbidden)}"


def _submit_matched_attempt(client: TestClient, *, student_id: str) -> None:
    response = client.post(
        "/attempts",
        headers={"X-Role": "student", "X-Student-Id": student_id},
        json={
            "item_id": "Q-001",
            "track": "core",
            "submitted_answer": "(x + 3)(x + 2)",
            "submitted_steps": ["(x + 3)(x + 2)"],
            "hint_level_used": 0,
        },
    )
    assert response.status_code == 201


def _submit_unmatched_attempt(client: TestClient, *, student_id: str) -> None:
    response = client.post(
        "/attempts",
        headers={"X-Role": "student", "X-Student-Id": student_id},
        json={
            "item_id": "Q-001",
            "track": "core",
            "submitted_answer": "(x + 3)(x + 2)",
            "submitted_steps": ["I used a different mental route."],
            "hint_level_used": 0,
        },
    )
    assert response.status_code == 201


if __name__ == "__main__":
    try:
        main()
    finally:
        DB_PATH.unlink(missing_ok=True)
