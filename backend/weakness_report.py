from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from backend.models import AttemptRecord, WeaknessReport


SUPPORT_ACTIONS = {
    "sign_error": (
        "repair_node={repair}; frequency={frequency}; suggested=5min sign review before next session",
        "A short five-minute review of sign changes before the next session would help."
    ),
    "calculation_error": (
        "repair_node={repair}; frequency={frequency}; suggested=written arithmetic check before next algebra step",
        "A short written arithmetic check before moving to the next algebra step would help."
    ),
    "formula_memory_error": (
        "repair_node={repair}; frequency={frequency}; suggested=formula structure before substitution",
        "Ask her to write the formula structure first, before substituting numbers."
    ),
    "conceptual_misunderstanding": (
        "repair_node={repair}; frequency={frequency}; suggested=one worked example then independent retry",
        "One focused worked example before another independent attempt would help reconnect the concept."
    ),
    "problem_interpretation_error": (
        "repair_node={repair}; frequency={frequency}; suggested=underline command word and required final form",
        "Underline the command word and required final form before starting."
    ),
    "strategy_selection_error": (
        "repair_node={repair}; frequency={frequency}; suggested=method choice question before calculation",
        "Before calculating, ask which method best fits the form of the question."
    ),
    "checking_finalization_error": (
        "repair_node={repair}; frequency={frequency}; suggested=final-line answer-form check",
        "A final line check for answer form, units, both roots, and the command word would help."
    ),
    "time_pressure_error": (
        "repair_node={repair}; frequency={frequency}; suggested=untimed retry before timed retry",
        "Use a slower untimed retry first, then add time pressure later."
    ),
}


def build_weakness_report(
    *,
    student_id: str,
    attempts: list[AttemptRecord],
    generated_at: datetime,
    window_days: int = 14,
) -> WeaknessReport:
    cutoff = generated_at - timedelta(days=window_days)
    window = [attempt for attempt in attempts if attempt.attempted_at >= cutoff]
    incorrect = [attempt for attempt in window if not attempt.correct]
    error_counts = Counter(attempt.error_category for attempt in incorrect if attempt.error_category)
    repair_counts = Counter(node for attempt in incorrect for node in attempt.repair_node_ids)

    top_error = error_counts.most_common(1)[0][0] if error_counts else None
    top_repair = repair_counts.most_common(1)[0][0] if repair_counts else None

    sentence = _latest_diagnostic_sentence(incorrect)
    if sentence is None and top_error:
        sentence = f"The most frequent recent issue is {top_error.replace('_', ' ')}."
    if sentence is None:
        sentence = "There is not enough recent error data to identify a stable stuck point yet."

    operator_template, parent_template = SUPPORT_ACTIONS.get(
        top_error or "",
        (
            "repair_node={repair}; frequency={frequency}; suggested=collect more attempts before recommendation",
            "Continue collecting attempts before making a strong support recommendation.",
        ),
    )
    frequency = error_counts.get(top_error, 0) if top_error else 0
    support_action_operator = operator_template.format(
        repair=top_repair or "none",
        frequency=f"{frequency}/{len(window)}",
    )

    return WeaknessReport(
        student_id=student_id,
        generated_at=generated_at,
        window_days=window_days,
        attempts_count=len(window),
        correct_count=sum(attempt.correct for attempt in window),
        top_error_category=top_error,
        top_repair_node_id=top_repair,
        stuck_point_sentence=sentence,
        support_action_operator=support_action_operator,
        support_action_parent=parent_template,
    )


def _latest_diagnostic_sentence(attempts: list[AttemptRecord]) -> str | None:
    for attempt in reversed(attempts):
        if attempt.diagnostic_sentence:
            return attempt.diagnostic_sentence
    return None
