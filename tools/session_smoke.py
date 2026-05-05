from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.item_bank import ItemBank
from backend.mastery import calculate_mastery_vectors
from backend.models import AttemptRecord, Track
from backend.persistence import LearningStore
from backend.session_engine import SessionEngine


def main() -> None:
    root = ROOT
    bank = ItemBank.from_directory_tree(root / "content" / "quadratics" / "items")
    engine = SessionEngine(bank)

    db_path = ROOT / ".tmp" / "session_smoke.sqlite"
    db_path.parent.mkdir(exist_ok=True)
    db_path.unlink(missing_ok=True)
    store = LearningStore(db_path)
    student_id = "sumin-demo"

    attempts = store.list_attempts(student_id)
    if not attempts:
        q1 = bank.get("Q-001")
        store.add_attempt(
            student_id,
            AttemptRecord(
                item_id=q1.id,
                concept_ids=tuple(q1.concept_ids),
                track=Track.CORE,
                correct=False,
                hint_level_used=2,
                attempted_at=datetime(2026, 5, 3, 18, 0, 0),
                error_category="strategy_selection_error",
                repair_node_ids=("quad.factorise_monic", "num.integer_arithmetic"),
            ),
        )
        q2 = bank.get("Q-002")
        store.add_attempt(
            student_id,
            AttemptRecord(
                item_id=q2.id,
                concept_ids=tuple(q2.concept_ids),
                track=Track.CORE,
                correct=True,
                hint_level_used=1,
                attempted_at=datetime(2026, 5, 3, 18, 8, 0),
                transfer_variation_of=q2.transfer_variation_of,
                articulation_ok=True,
            ),
        )
        attempts = store.list_attempts(student_id)

    plan = engine.build_daily_plan(student_id=student_id, session_date=date(2026, 5, 3), attempts=attempts)
    mastery = calculate_mastery_vectors(attempts)

    print("core", [task.item_id for task in plan.core])
    print("repair", [(task.item_id, task.reason) for task in plan.repair])
    print("explore", [(task.item_id, task.locked) for task in plan.explore])
    print("mastery", {key: value for key, value in mastery.items()})


if __name__ == "__main__":
    main()
