from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ITEM_ROOT = ROOT / "content" / "quadratics" / "items"

DEFICIT_TERMS = ("cannot", "struggle", "weak", "failing", "behind", "gap", "wrong", "mistake", "error")


def main() -> None:
    failures: list[dict[str, Any]] = []
    for path in sorted(ITEM_ROOT.glob("*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for field_name, value in student_visible_texts(data):
            lower = value.lower()
            hits = [term for term in DEFICIT_TERMS if term in lower]
            if hits:
                failures.append(
                    {
                        "item": data.get("id", path.name),
                        "field": field_name,
                        "terms": hits,
                        "text": value,
                    }
                )
    print(json.dumps({"passed": not failures, "failures": failures}, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


def student_visible_texts(data: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = [
        ("title", data.get("title", "")),
        ("problem_text", data.get("problem_text", "")),
        ("student_prompt", data.get("student_prompt", "")),
        ("metacognition_prompt", data.get("metacognition_prompt") or ""),
    ]
    for mapping in data.get("error_category_mapping", []):
        fields.append((f"mapping.{mapping.get('code')}.diagnostic_sentence", mapping.get("diagnostic_sentence", "")))
    for hint in data.get("hint_ladder", []):
        fields.append((f"hint.{hint.get('level')}.title", hint.get("title", "")))
        fields.append((f"hint.{hint.get('level')}.prompt", hint.get("prompt", "")))
    for step in data.get("expected_solution_steps", []):
        fields.append((f"step.{step.get('step_number')}.diagnostic_sentence", step.get("diagnostic_sentence", "")))
    return [(name, value) for name, value in fields if value]


if __name__ == "__main__":
    main()
