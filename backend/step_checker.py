from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from schema.item import ErrorMappingEntry, Item, SolutionStep


class StepStatus(StrEnum):
    MATCHED_EXPECTED = "matched_expected"
    LIKELY_ERROR = "likely_error"
    UNMATCHED = "unmatched"


@dataclass(frozen=True)
class StepCheck:
    submitted_index: int
    submitted_text: str
    status: StepStatus
    expected_step_number: int | None = None
    diagnostic_target: str | None = None
    diagnostic_sentence: str | None = None
    selected_error_code: str | None = None


def check_submitted_steps(item: Item, submitted_steps: tuple[str, ...]) -> tuple[StepCheck, ...]:
    checks: list[StepCheck] = []
    for index, submitted in enumerate(submitted_steps, start=1):
        checks.append(_check_one_step(index, submitted, item))
    return tuple(checks)


def first_error_code_from_steps(checks: tuple[StepCheck, ...]) -> str | None:
    for check in checks:
        if check.status == StepStatus.LIKELY_ERROR and check.selected_error_code:
            return check.selected_error_code
    return None


def _check_one_step(index: int, submitted: str, item: Item) -> StepCheck:
    norm = _normalise(submitted)
    if not norm:
        return StepCheck(index, submitted, StepStatus.UNMATCHED)

    trigger_match = _match_error_trigger(norm, item.error_category_mapping)
    if trigger_match is not None:
        return StepCheck(
            submitted_index=index,
            submitted_text=submitted,
            status=StepStatus.LIKELY_ERROR,
            expected_step_number=trigger_match.expected_step_number,
            diagnostic_target=trigger_match.diagnostic_target,
            diagnostic_sentence=trigger_match.diagnostic_sentence,
            selected_error_code=trigger_match.code,
        )

    expected_match = _match_expected_expression(norm, item.expected_solution_steps)
    if expected_match is not None:
        return StepCheck(
            submitted_index=index,
            submitted_text=submitted,
            status=StepStatus.MATCHED_EXPECTED,
            expected_step_number=expected_match.step_number,
            diagnostic_target=expected_match.diagnostic_target,
            diagnostic_sentence=expected_match.diagnostic_sentence,
        )

    common_error_match = _match_common_error(norm, item.expected_solution_steps)
    if common_error_match is not None:
        return StepCheck(
            submitted_index=index,
            submitted_text=submitted,
            status=StepStatus.LIKELY_ERROR,
            expected_step_number=common_error_match.step_number,
            diagnostic_target=common_error_match.diagnostic_target,
            diagnostic_sentence=common_error_match.diagnostic_sentence,
        )

    return StepCheck(index, submitted, StepStatus.UNMATCHED)


def _match_error_trigger(norm: str, mappings: list[ErrorMappingEntry]) -> ErrorMappingEntry | None:
    for mapping in mappings:
        trigger = _normalise(mapping.trigger)
        if trigger and trigger in norm:
            return mapping
    return None


def _match_expected_expression(norm: str, steps: list[SolutionStep]) -> SolutionStep | None:
    for step in steps:
        expr = _normalise(step.expression)
        if expr and (expr in norm or norm in expr):
            return step
    return None


def _match_common_error(norm: str, steps: list[SolutionStep]) -> SolutionStep | None:
    for step in steps:
        for error in step.common_errors:
            err = _normalise(error)
            if err and (err in norm or norm in err):
                return step
    return None


def _normalise(value: str) -> str:
    return (
        value.lower()
        .replace("−", "-")
        .replace("²", "^2")
        .replace(" ", "")
        .replace("*", "")
    )

