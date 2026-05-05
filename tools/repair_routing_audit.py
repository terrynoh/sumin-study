from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.item_bank import ItemBank
from backend.models import AttemptRecord, Track
from backend.session_engine import SessionEngine
from schema.stuck_point import StudentAttempt, match_stuck_point


SCENARIO_RE = re.compile(r"Called by (Q-\d{3}) ([A-Z0-9_]+)")


def main() -> None:
    bank = ItemBank.from_directory_tree(ROOT / "content" / "quadratics" / "items")
    extended = bank.by_tier("extended")
    core = bank.by_tier("core_repair")
    unmatched_nodes = _audit_node_coverage(bank, extended)
    scenario_failures = _audit_scenario_routing(bank, core)
    atomic_failures = _audit_atomic_gate(core)

    result = {
        "passed": not unmatched_nodes and not scenario_failures and not atomic_failures,
        "extended_items": len(extended),
        "core_repair_items": len(core),
        "unmatched_nodes": unmatched_nodes,
        "scenario_failures": scenario_failures,
        "atomic_gate_failures": atomic_failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


def _audit_node_coverage(bank: ItemBank, extended) -> dict[str, str]:
    nodes: set[str] = set()
    for item in extended:
        for mapping in item.error_category_mapping:
            nodes.update(mapping.repair_node_ids)
    return {
        node_id: "no core_repair item"
        for node_id in sorted(nodes)
        if not bank.core_repair_items_for(node_id)
    }


def _audit_scenario_routing(bank: ItemBank, core) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    engine = SessionEngine(bank)
    for cr_item in core:
        scenarios = _scenarios_for(cr_item)
        if not scenarios:
            failures.append({"cr_id": cr_item.id, "expected_scenario": "missing", "actual_routed_to": "none"})
            continue
        for qid, code in scenarios:
            extended_item = bank.get(qid)
            mapping = next((entry for entry in extended_item.error_category_mapping if entry.code == code), None)
            if mapping is None:
                failures.append({"cr_id": cr_item.id, "expected_scenario": f"{qid} {code}", "actual_routed_to": "missing error code"})
                continue
            stuck = match_stuck_point(
                extended_item,
                StudentAttempt(item_id=qid, selected_error_code=code, hint_level_used=0),
            )
            attempts: list[AttemptRecord] = []
            _mark_prior_core_repair_candidates_as_seen(bank, attempts, cr_item, stuck.repair_node_ids)
            attempts.append(
                AttemptRecord(
                    item_id=qid,
                    concept_ids=tuple(extended_item.concept_ids),
                    track=Track.CORE,
                    correct=False,
                    hint_level_used=0,
                    attempted_at=datetime(2026, 5, 3, 18, 0, 0),
                    error_category=None if stuck.category is None else str(stuck.category),
                    repair_node_ids=tuple(stuck.repair_node_ids),
                )
            )
            repair = engine.build_daily_plan(
                student_id="audit",
                session_date=datetime(2026, 5, 3).date(),
                attempts=attempts,
            ).repair
            actual = repair[0].item_id if repair else "none"
            if actual != cr_item.id:
                failures.append({"cr_id": cr_item.id, "expected_scenario": f"{qid} {code}", "actual_routed_to": actual})
    return failures


def _mark_prior_core_repair_candidates_as_seen(
    bank: ItemBank,
    attempts: list[AttemptRecord],
    cr_item,
    repair_node_ids: list[str],
) -> None:
    for node_id in repair_node_ids:
        candidates = bank.core_repair_items_for(node_id)
        if cr_item not in candidates:
            continue
        for candidate in candidates:
            if candidate.id == cr_item.id:
                return
            attempts.append(
                AttemptRecord(
                    item_id=candidate.id,
                    concept_ids=tuple(candidate.concept_ids),
                    track=Track.REPAIR,
                    correct=True,
                    hint_level_used=0,
                    attempted_at=datetime(2026, 5, 3, 18, 5, 0),
                )
            )


def _scenarios_for(item) -> list[tuple[str, str]]:
    text = f"{item.source_reference.notes} {item.mark_scheme_notes}"
    return list(dict.fromkeys(SCENARIO_RE.findall(text)))


def _audit_atomic_gate(core) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    required = ["Atomicity:", "Scenario:", "Surface variation:", "No new vocab:", "Single-step or two-step:"]
    for item in core:
        notes = f"{item.source_reference.notes} {item.mark_scheme_notes}"
        missing = [key for key in required if key not in notes]
        if missing:
            failures.append({"cr_id": item.id, "missing": ", ".join(missing)})
        if len(item.expected_solution_steps) > 2:
            failures.append({"cr_id": item.id, "missing": "expected_solution_steps > 2"})
    return failures


if __name__ == "__main__":
    main()
