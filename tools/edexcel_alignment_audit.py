from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from schema.item import load_graph, load_item


FORBIDDEN_TERMS = ("Cambridge", "0580", "cambridge_style_original")
TEXT_FILES_TO_SCAN = [
    ROOT / "MVP_SPEC.md",
    ROOT / "docs" / "DESIGN_BRIEF.md",
    ROOT / "docs" / "API_SPEC.md",
    ROOT / "schema" / "item.py",
    ROOT / "app" / "schemas.py",
]
ITEM_ROOT = ROOT / "content" / "quadratics" / "items"
GRAPH_PATH = ROOT / "content" / "quadratics" / "concept_graph.json"


def main() -> None:
    checks = [
        check_source_text_has_no_old_board_terms,
        check_graph_metadata,
        check_items_load_and_validate_against_graph,
        check_items_have_edexcel_metadata,
        check_no_non_calculator_strategy_refs,
    ]
    results: list[dict[str, Any]] = []
    failed = False
    for check in checks:
        try:
            detail = check()
            results.append({"check": check.__name__, "passed": True, **detail})
        except AssertionError as exc:
            failed = True
            results.append({"check": check.__name__, "passed": False, "error": str(exc)})
    print(json.dumps({"passed": not failed, "results": results}, indent=2, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


def check_source_text_has_no_old_board_terms() -> dict[str, Any]:
    hits: list[str] = []
    for path in TEXT_FILES_TO_SCAN:
        text = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_TERMS:
            if term in text:
                hits.append(f"{path.relative_to(ROOT)} contains {term!r}")
    assert not hits, "; ".join(hits)
    return {"files_scanned": len(TEXT_FILES_TO_SCAN)}


def check_graph_metadata() -> dict[str, Any]:
    data = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    exam_board = data["exam_board"]
    assert exam_board["board"] == "Pearson Edexcel International GCSE Mathematics A"
    assert exam_board["syllabus_code"] == "4MA1"
    assert exam_board["primary_tier"] == "higher"
    assert exam_board["repair_tier"] == "foundation_prerequisite_repair"
    assert exam_board["student_stage"] == "Year 10"
    assert exam_board["paper_codes"] == ["4MA1/1H", "4MA1/2H"]
    text = GRAPH_PATH.read_text(encoding="utf-8")
    for term in FORBIDDEN_TERMS:
        assert term not in text, f"{GRAPH_PATH.relative_to(ROOT)} contains {term!r}"
    return {"nodes": len(data["nodes"])}


def check_items_load_and_validate_against_graph() -> dict[str, Any]:
    graph = load_graph(GRAPH_PATH)
    count = 0
    for path in item_paths():
        item = load_item(path)
        item.validate_against_graph(graph)
        count += 1
    return {"items": count}


def check_items_have_edexcel_metadata() -> dict[str, Any]:
    missing: list[str] = []
    invalid: list[str] = []
    required = {
        "exam_board",
        "syllabus_code",
        "tier_target",
        "paper_codes",
        "syllabus_refs",
        "calculator_policy",
        "source_style",
        "year10_sequence_band",
        "transfer_axis",
    }
    for path in item_paths():
        data = json.loads(path.read_text(encoding="utf-8"))
        item_name = path.relative_to(ROOT).as_posix()
        missing_fields = sorted(field for field in required if not data.get(field))
        if missing_fields:
            missing.append(f"{item_name}: {missing_fields}")
        if data.get("source_reference", {}).get("source_type") != "edexcel_style_original":
            invalid.append(f"{item_name}: source_reference.source_type")
        if data.get("source_style") != "edexcel_style_original":
            invalid.append(f"{item_name}: source_style")
        if data.get("exam_board") != "edexcel_igcse_math_a":
            invalid.append(f"{item_name}: exam_board")
        if data.get("syllabus_code") != "4MA1":
            invalid.append(f"{item_name}: syllabus_code")
        if data.get("calculator_policy") != "calculator_allowed":
            invalid.append(f"{item_name}: calculator_policy")
        if data.get("tier") == "extended" and data.get("tier_target") != "higher":
            invalid.append(f"{item_name}: tier_target")
        if data.get("tier") == "core_repair" and data.get("tier_target") != "foundation_prerequisite_repair":
            invalid.append(f"{item_name}: tier_target")
        for term in FORBIDDEN_TERMS:
            if term in path.read_text(encoding="utf-8"):
                invalid.append(f"{item_name}: contains {term!r}")
    assert not missing, "; ".join(missing)
    assert not invalid, "; ".join(invalid)
    return {"items": len(item_paths())}


def check_no_non_calculator_strategy_refs() -> dict[str, Any]:
    hits: list[str] = []
    for path in [GRAPH_PATH, *item_paths()]:
        text = path.read_text(encoding="utf-8")
        if "exam.non_calculator_strategy" in text or "Non-calculator strategy" in text:
            hits.append(path.relative_to(ROOT).as_posix())
    assert not hits, "; ".join(hits)
    return {"files_scanned": len(item_paths()) + 1}


def item_paths() -> list[Path]:
    return sorted(ITEM_ROOT.glob("*/*.json"))


if __name__ == "__main__":
    main()
