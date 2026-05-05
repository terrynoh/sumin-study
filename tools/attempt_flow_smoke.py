from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.attempt_service import AttemptService, AttemptSubmission
from backend.item_bank import ItemBank
from backend.models import Track
from backend.persistence import LearningStore


def main() -> None:
    bank = ItemBank.from_directory(ROOT / "content" / "quadratics" / "items" / "extended")
    db_path = ROOT / ".tmp" / "attempt_flow_smoke.sqlite"
    db_path.parent.mkdir(exist_ok=True)
    db_path.unlink(missing_ok=True)
    store = LearningStore(db_path)
    service = AttemptService(bank, store)

    outcome = service.submit(
        student_id="sumin-attempt-smoke",
        submission=AttemptSubmission(
            item_id="Q-005",
            track=Track.CORE,
            submitted_answer="(x - 3)(x - 5)",
            hint_level_used=2,
        ),
        attempted_at=datetime(2026, 5, 3, 19, 0, 0),
    )

    print("correct", outcome.check.correct)
    print("error_code", outcome.check.selected_error_code)
    print("stuck", None if outcome.stuck_point is None else outcome.stuck_point.diagnostic_target)
    print("next_track", outcome.next_track.value)


if __name__ == "__main__":
    main()
