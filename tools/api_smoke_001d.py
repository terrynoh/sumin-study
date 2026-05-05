from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / ".tmp" / "api_smoke_001d.sqlite"
DB_PATH.parent.mkdir(exist_ok=True)
DB_PATH.unlink(missing_ok=True)
os.environ["SUMIN_STUDY_DB_PATH"] = str(DB_PATH)

from fastapi.testclient import TestClient

from app.main import app


def headers(role: str, student_id: str = "parent-demo") -> dict[str, str]:
    return {"X-Role": role, "X-Student-Id": student_id}


def main() -> None:
    with TestClient(app) as client:
        tests = [
            test_parent_endpoints_require_parent_role,
            test_parent_endpoints_missing_role_422,
            test_weekly_summary_created_on_demand,
            test_weekly_summary_strips_operator_and_raw_fields,
            test_weekly_summary_uses_week_bounds,
            test_mark_sent_with_empty_body,
            test_mark_sent_with_explicit_sent_at,
            test_sent_status_persists_after_regeneration,
        ]
        for test in tests:
            test(client)
            print(f"PASS {test.__name__}")


def test_parent_endpoints_require_parent_role(client: TestClient) -> None:
    for role in ("student", "operator"):
        response = client.get("/parent/weekly-summary", headers=headers(role, "role-parent"))
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "ROLE_MISMATCH"


def test_parent_endpoints_missing_role_422(client: TestClient) -> None:
    response = client.get("/parent/weekly-summary")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_weekly_summary_created_on_demand(client: TestClient) -> None:
    student_id = "summary-create"
    _submit_sign_error(client, student_id)
    response = client.get("/parent/weekly-summary?as_of=2026-05-03", headers=headers("parent", student_id))
    assert response.status_code == 200
    data = response.json()
    assert data["week_start"] == "2026-04-27"
    assert data["week_end"] == "2026-05-03"
    assert data["draft_status"] == "unsent"
    assert data["sent_at"] is None
    assert data["improving"]
    assert data["still_developing"]
    assert data["one_thing_that_would_help"]
    assert client.app.state.store.get_parent_summary(student_id, _date(2026, 4, 27)) is not None


def test_weekly_summary_strips_operator_and_raw_fields(client: TestClient) -> None:
    student_id = "summary-privacy"
    _submit_sign_error(client, student_id)
    response = client.get("/parent/weekly-summary?as_of=2026-05-03", headers=headers("parent", student_id))
    assert response.status_code == 200
    data = response.json()
    forbidden = {
        "attempts_count",
        "correct_count",
        "top_repair_node_id",
        "top_error_category",
        "support_action_operator",
        "support_action_parent",
        "submitted_steps",
        "submitted_answer",
        "reflection_text",
    }
    assert not (forbidden & set(data))


def test_weekly_summary_uses_week_bounds(client: TestClient) -> None:
    response = client.get("/parent/weekly-summary?as_of=2026-05-06", headers=headers("parent", "week-bounds"))
    assert response.status_code == 200
    data = response.json()
    assert data["week_start"] == "2026-05-04"
    assert data["week_end"] == "2026-05-10"


def test_mark_sent_with_empty_body(client: TestClient) -> None:
    student_id = "summary-sent-empty"
    response = client.post("/parent/weekly-summary/sent?as_of=2026-05-03", headers=headers("parent", student_id))
    assert response.status_code == 200
    data = response.json()
    assert data["draft_status"] == "sent"
    assert data["sent_at"] is not None


def test_mark_sent_with_explicit_sent_at(client: TestClient) -> None:
    student_id = "summary-sent-explicit"
    response = client.post(
        "/parent/weekly-summary/sent?as_of=2026-05-03",
        headers=headers("parent", student_id),
        json={"sent_at": "2026-05-03T20:00:00"},
    )
    assert response.status_code == 200
    assert response.json()["sent_at"] == "2026-05-03T20:00:00"


def test_sent_status_persists_after_regeneration(client: TestClient) -> None:
    student_id = "summary-sent-persist"
    response = client.post(
        "/parent/weekly-summary/sent?as_of=2026-05-03",
        headers=headers("parent", student_id),
        json={"sent_at": "2026-05-03T21:00:00"},
    )
    assert response.status_code == 200
    _submit_sign_error(client, student_id)
    response = client.get("/parent/weekly-summary?as_of=2026-05-03", headers=headers("parent", student_id))
    assert response.status_code == 200
    data = response.json()
    assert data["draft_status"] == "sent"
    assert data["sent_at"] == "2026-05-03T21:00:00"


def _submit_sign_error(client: TestClient, student_id: str) -> None:
    response = client.post(
        "/attempts",
        headers=headers("student", student_id),
        json={
            "item_id": "Q-005",
            "track": "core",
            "submitted_answer": "x = -3 or x = -5",
            "submitted_steps": ["x + 3 = 0"],
            "selected_error_code": "Q005_FACTOR_SIGNS",
        },
    )
    assert response.status_code == 201, response.text


def _date(year: int, month: int, day: int):
    from datetime import date

    return date(year, month, day)


if __name__ == "__main__":
    try:
        main()
    finally:
        DB_PATH.unlink(missing_ok=True)
