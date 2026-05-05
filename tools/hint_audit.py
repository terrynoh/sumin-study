from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_GENERIC_PATTERNS = {
    "x^2 + bx + c",
    "ax^2 + bx + c",
    "(x + p)(x + q)",
    "b^2 - 4ac",
    "(x - h)^2 + k",
    "(x + a)^2 + b",
}


def normalise(text: str) -> str:
    return " ".join(text.lower().replace("−", "-").split())


def audit_item(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: list[dict[str, str]] = []
    expected_answer = normalise(data.get("expected_answer", ""))
    for hint in data.get("hint_ladder", []):
        prompt = normalise(hint.get("prompt", ""))
        level = str(hint.get("level", "?"))
        if expected_answer and expected_answer in prompt:
            problems.append(
                {
                    "item": data.get("id", path.name),
                    "level": level,
                    "reason": "hint prompt contains expected_answer",
                    "text": hint.get("prompt", ""),
                }
            )
        for step in data.get("expected_solution_steps", []):
            expr = normalise(step.get("expression", ""))
            if not expr or expr in {normalise(p) for p in ALLOWED_GENERIC_PATTERNS}:
                continue
            if expr in prompt:
                problems.append(
                    {
                        "item": data.get("id", path.name),
                        "level": level,
                        "reason": f"hint prompt contains expected_solution_steps expression for step {step.get('step_number')}",
                        "text": hint.get("prompt", ""),
                    }
                )
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit hint ladders for answer leakage.")
    parser.add_argument("items", nargs="+", help="Item JSON files")
    args = parser.parse_args()

    all_problems: list[dict[str, str]] = []
    for raw_path in args.items:
        all_problems.extend(audit_item(Path(raw_path)))

    print(json.dumps({"passed": not all_problems, "violations": all_problems}, ensure_ascii=False, indent=2))
    if all_problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

