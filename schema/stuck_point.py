from __future__ import annotations

from pydantic import BaseModel, Field

from schema.item import ErrorCategory, Item


class StudentStep(BaseModel):
    step_number: int = Field(ge=1)
    text: str


class StudentAttempt(BaseModel):
    item_id: str
    final_answer: str | None = None
    submitted_steps: list[StudentStep] = Field(default_factory=list)
    selected_error_code: str | None = None
    hint_level_used: int = Field(default=0, ge=0, le=4)


class StuckPointMatch(BaseModel):
    matched: bool
    item_id: str
    error_code: str | None = None
    category: ErrorCategory | None = None
    expected_step_number: int | None = None
    diagnostic_target: str | None = None
    diagnostic_sentence: str
    repair_node_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    fallback: bool = False


def match_stuck_point(item: Item, attempt: StudentAttempt) -> StuckPointMatch:
    """Static v1 matcher.

    v1 deliberately avoids LLM diagnosis. It first accepts an explicit
    selected_error_code from answer checking. If none exists, it scans student
    step text for common-error trigger phrases. If still unmatched, it returns
    the agreed safe fallback instead of pretending to know the cause.
    """

    if attempt.selected_error_code:
        for mapping in item.error_category_mapping:
            if mapping.code == attempt.selected_error_code:
                return StuckPointMatch(
                    matched=True,
                    item_id=item.id,
                    error_code=mapping.code,
                    category=mapping.category,
                    expected_step_number=mapping.expected_step_number,
                    diagnostic_target=mapping.diagnostic_target,
                    diagnostic_sentence=mapping.diagnostic_sentence,
                    repair_node_ids=mapping.repair_node_ids,
                    confidence=0.9,
                )

    joined_steps = "\n".join(step.text.lower() for step in attempt.submitted_steps)
    for mapping in item.error_category_mapping:
        trigger = mapping.trigger.lower()
        if trigger and trigger in joined_steps:
            return StuckPointMatch(
                matched=True,
                item_id=item.id,
                error_code=mapping.code,
                category=mapping.category,
                expected_step_number=mapping.expected_step_number,
                diagnostic_target=mapping.diagnostic_target,
                diagnostic_sentence=mapping.diagnostic_sentence,
                repair_node_ids=mapping.repair_node_ids,
                confidence=0.55,
            )

    return StuckPointMatch(
        matched=False,
        item_id=item.id,
        diagnostic_sentence=(
            "I am not sure exactly where the issue is yet. "
            "Let's compare your next step with the standard solution path."
        ),
        confidence=0.0,
        fallback=True,
    )

