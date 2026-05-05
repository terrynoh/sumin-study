from __future__ import annotations

import re
from dataclasses import dataclass

from schema.item import Item


@dataclass(frozen=True)
class AnswerCheckResult:
    correct: bool
    method: str
    selected_error_code: str | None = None
    feedback: str = ""


def check_answer(item: Item, submitted_answer: str) -> AnswerCheckResult:
    """Dependency-free v1 answer checker.

    This is intentionally conservative. It handles the current 20 active
    quadratic items without pulling in SymPy. Future symbolic checking can
    replace this module behind the same result shape.
    """

    submitted = _normalise(submitted_answer)
    expected = _normalise(item.expected_answer)

    if not submitted:
        return _incorrect(item, submitted, "blank", "No answer was submitted.")

    if submitted == expected:
        return AnswerCheckResult(True, "exact_normalised", feedback="Correct.")

    if item.notation_style == "factorised_form" and _factorised_equivalent(submitted, expected):
        return AnswerCheckResult(True, "factorised_bracket_order", feedback="Correct.")

    if _or_answer_equivalent(submitted, expected):
        return AnswerCheckResult(True, "unordered_or_answer", feedback="Correct.")

    if _component_answer_equivalent(submitted, expected):
        return AnswerCheckResult(True, "component_match", feedback="Correct.")

    return _incorrect(item, submitted, "rule_based_incorrect", "The answer does not match the expected result.")


def _incorrect(item: Item, submitted: str, method: str, feedback: str) -> AnswerCheckResult:
    code = _infer_error_code(item, submitted)
    return AnswerCheckResult(False, method, selected_error_code=code, feedback=feedback)


def _infer_error_code(item: Item, submitted: str) -> str | None:
    for mapping in item.error_category_mapping:
        trigger = _normalise(mapping.trigger)
        if trigger and trigger in submitted:
            return mapping.code
    return None


def _normalise(value: str) -> str:
    value = value.lower()
    value = value.replace("−", "-")
    value = value.replace("²", "^2")
    value = value.replace("×", "x")
    value = value.replace(";", " or ")
    value = re.sub(r"\s+", "", value)
    return value


def _factorised_equivalent(submitted: str, expected: str) -> bool:
    return sorted(_brackets(submitted)) == sorted(_brackets(expected)) and bool(_brackets(expected))


def _brackets(value: str) -> list[str]:
    return re.findall(r"\([^()]+\)", value)


def _or_answer_equivalent(submitted: str, expected: str) -> bool:
    if "or" not in expected:
        return False
    return sorted(filter(None, expected.split("or"))) == sorted(filter(None, submitted.split("or")))


def _component_answer_equivalent(submitted: str, expected: str) -> bool:
    """Check common multi-part answers without requiring exact wording."""

    if "no real roots" in expected:
        return "-12" in submitted and "noreal" in submitted

    if "turningpoint" in expected:
        expected_numbers = set(re.findall(r"-?\d+(?:\.\d+)?", expected))
        submitted_numbers = set(re.findall(r"-?\d+(?:\.\d+)?", submitted))
        return expected_numbers.issubset(submitted_numbers)

    if "x-intercepts" in expected or "y-intercept" in expected:
        expected_numbers = set(re.findall(r"-?\d+(?:\.\d+)?", expected))
        submitted_numbers = set(re.findall(r"-?\d+(?:\.\d+)?", submitted))
        return expected_numbers.issubset(submitted_numbers)

    if "maximumheight" in expected:
        return "16" in submitted and "3" in submitted and ("max" in submitted or "maximum" in submitted)

    if expected == "8and9":
        return "8" in submitted and "9" in submitted

    if expected == "x=7" or expected == "x=5" or expected == "x=4":
        return expected in submitted

    return False

