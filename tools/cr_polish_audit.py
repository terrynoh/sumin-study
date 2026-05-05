from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "content" / "quadratics" / "items" / "core"

PLACEHOLDER_PREFIXES = (
    "the repair target is",
    "the stuck point is",
)
GENERIC_TRIGGERS = {
    "not sure",
    "answer",
    "x",
    "wrong",
    "error",
    "mistake",
}


def main() -> None:
    items = [_load(path) for path in sorted(CORE_DIR.glob("CR-*.json"))]
    failures: list[dict[str, str]] = []
    failures.extend(_audit_hint_similarity(items))
    failures.extend(_audit_diagnostic_sentences(items))
    failures.extend(_audit_triggers(items))

    result = {
        "passed": not failures,
        "items_checked": len(items),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["_path"] = str(path)
    return data


def _audit_hint_similarity(items: list[dict]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    exact_by_level: dict[int, Counter[str]] = defaultdict(Counter)
    owners: dict[tuple[int, str], list[str]] = defaultdict(list)
    ngram_owners: dict[tuple[int, str], set[str]] = defaultdict(set)

    for item in items:
        for hint in item["hint_ladder"]:
            level = hint["level"]
            normalised = _normalise(hint["prompt"])
            exact_by_level[level][normalised] += 1
            owners[(level, normalised)].append(item["id"])
            for ngram in _word_ngrams(normalised, 5):
                ngram_owners[(level, ngram)].add(item["id"])

    for level, prompts in exact_by_level.items():
        for prompt, count in prompts.items():
            if count >= 5:
                failures.append(
                    {
                        "check": "hint_similarity_exact",
                        "level": str(level),
                        "items": ",".join(owners[(level, prompt)]),
                        "detail": "same normalised prompt appears in 5 or more CR items",
                    }
                )

    for (level, ngram), item_ids in ngram_owners.items():
        if len(item_ids) >= 5:
            failures.append(
                {
                    "check": "hint_similarity_ngram",
                    "level": str(level),
                    "items": ",".join(sorted(item_ids)),
                    "detail": f"5-word phrase repeated across 5 or more CR items: {ngram}",
                }
            )
    return failures


def _audit_diagnostic_sentences(items: list[dict]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for item in items:
        diagnostics: list[tuple[str, str]] = []
        for mapping in item["error_category_mapping"]:
            diagnostics.append(("error_category_mapping", mapping["diagnostic_sentence"]))
        for step in item["expected_solution_steps"]:
            diagnostics.append(("expected_solution_steps", step["diagnostic_sentence"]))

        for location, sentence in diagnostics:
            lowered = sentence.strip().lower()
            if any(lowered.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES):
                failures.append(
                    {
                        "check": "diagnostic_placeholder",
                        "item_id": item["id"],
                        "location": location,
                        "detail": "diagnostic sentence starts with a placeholder prefix",
                    }
                )
            if len(sentence.strip()) < 60:
                failures.append(
                    {
                        "check": "diagnostic_length",
                        "item_id": item["id"],
                        "location": location,
                        "detail": "diagnostic sentence is shorter than 60 characters",
                    }
                )
    return failures


def _audit_triggers(items: list[dict]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    seen: dict[str, list[str]] = defaultdict(list)
    for item in items:
        for mapping in item["error_category_mapping"]:
            trigger = mapping["trigger"].strip().lower()
            seen[trigger].append(item["id"])
            if trigger in GENERIC_TRIGGERS:
                failures.append(
                    {
                        "check": "trigger_generic",
                        "item_id": item["id"],
                        "detail": f"generic trigger: {trigger}",
                    }
                )
            if len(trigger) < 2:
                failures.append(
                    {
                        "check": "trigger_too_short",
                        "item_id": item["id"],
                        "detail": f"trigger too short: {trigger}",
                    }
                )

    for trigger, item_ids in seen.items():
        if len(item_ids) >= 3:
            failures.append(
                {
                    "check": "trigger_repeated",
                    "items": ",".join(item_ids),
                    "detail": f"trigger repeated across 3 or more CR items: {trigger}",
                }
            )
    return failures


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9^=+\- ]+", " ", text.lower())).strip()


def _word_ngrams(text: str, size: int) -> set[str]:
    words = text.split()
    return {" ".join(words[index : index + size]) for index in range(0, len(words) - size + 1)}


if __name__ == "__main__":
    main()
