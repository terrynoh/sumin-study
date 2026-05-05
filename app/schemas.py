from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HintRung(BaseModel):
    level: int
    title: str
    prompt: str


class ItemForStudent(BaseModel):
    id: str
    title: str
    tier: Literal["extended", "core_repair"]
    student_facing_language: str
    problem_text: str
    student_prompt: str
    metacognition_prompt: str | None
    marks: int
    difficulty: int
    calculator_policy: str
    notation_style: str
    hint_ladder: list[HintRung]


class SessionTaskView(BaseModel):
    track: Literal["core", "repair", "explore", "stretch", "review"]
    item_id: str
    item_title: str
    reason: str
    locked: bool


class DailySessionPlanView(BaseModel):
    student_id: str
    session_date: date
    tasks: list[SessionTaskView]
    notes: list[str]


class MasteryVectorView(BaseModel):
    concept_id: str
    concept_name_en: str
    accuracy: Literal["ready", "developing", "not_checked"]
    hint_independence: Literal["ready", "developing", "not_checked"]
    retention: Literal["ready", "developing", "not_checked"]
    transfer: Literal["ready", "developing", "not_checked"]
    articulation: Literal["ready", "developing", "not_checked"]
    mastered: bool


class MasterySnapshotView(BaseModel):
    student_id: str
    vectors: list[MasteryVectorView]
    generated_at: datetime


class RetentionDueView(BaseModel):
    item_id: str
    item_title: str
    concept_ids: list[str]
    first_correct_date: date
    days_since: int
    reason: str


class RetentionDueResponse(BaseModel):
    due: list[RetentionDueView]


class WeaknessReportStudentView(BaseModel):
    stuck_point_sentence: str
    mastery_vectors: list[MasteryVectorView]


class HealthView(BaseModel):
    status: Literal["ok"]
    item_bank: dict[str, int | str]
    db_path: str
    uptime_seconds: int


class RepairContextDTO(BaseModel):
    original_item_id: str
    original_track: Literal["core", "repair", "explore", "stretch", "review"]
    repair_chain: list[str] = Field(default_factory=list)
    depth: int = 0
    escalated: bool = False


class AttemptSubmitRequest(BaseModel):
    item_id: str
    track: Literal["core", "repair", "explore", "stretch", "review"]
    submitted_answer: str
    submitted_steps: list[str] = Field(default_factory=list)
    hint_level_used: int = Field(default=0, ge=0, le=4)
    selected_error_code: str | None = None
    articulation_ok: bool | None = None
    repair_context: RepairContextDTO | None = None


class StepCheckView(BaseModel):
    submitted_index: int
    submitted_text: str
    status: str
    expected_step_number: int | None
    diagnostic_target: str | None
    diagnostic_sentence: str | None
    selected_error_code: str | None


class StuckPointView(BaseModel):
    matched: bool
    error_code: str | None
    category: str | None
    diagnostic_sentence: str
    repair_node_ids: list[str]
    fallback: bool


class AnswerCheckView(BaseModel):
    correct: bool
    method: str
    feedback: str


class AttemptOutcomeView(BaseModel):
    attempt_id: int
    item_id: str
    correct: bool
    feedback: str
    selected_error_code: str | None
    path_match_status: Literal["matched", "alternative", "unmatched", "n/a"]
    answer_check: AnswerCheckView
    stuck_point: StuckPointView | None
    step_checks: list[StepCheckView]
    next_item_id: str
    next_track: Literal["core", "repair", "explore", "stretch", "review"]
    repair_context_after: RepairContextDTO | None
    mastery_vectors: list[MasteryVectorView]


class ReflectionSubmitRequest(BaseModel):
    item_id: str
    reflection_text: str
    articulation_ok: bool | None = None


class ReflectionStoredView(BaseModel):
    stored: bool


class ItemBankGateStatus(BaseModel):
    concept_ids: str
    exam_literacy_ids: str
    prerequisite_ids: str
    error_category_mapping: str
    hint_ladder: str
    expected_solution_steps: str


class ItemBankEntryView(BaseModel):
    id: str
    title: str
    tier: Literal["extended", "core_repair"]
    status: Literal["draft", "active", "retired"]
    concept_ids: list[str]
    gates: ItemBankGateStatus
    attempt_count: int
    correct_ratio: float
    avg_hint_level: float


class ItemBankListResponse(BaseModel):
    items: list[ItemBankEntryView]


class ErrorMappingView(BaseModel):
    code: str
    category: str
    trigger: str
    expected_step_number: int
    diagnostic_target: str
    diagnostic_sentence: str
    repair_node_ids: list[str]


class SolutionStepView(BaseModel):
    step_number: int
    action: str
    expression: str
    diagnostic_target: str
    common_errors: list[str]
    diagnostic_sentence: str


class ItemForOperator(BaseModel):
    id: str
    title: str
    tier: Literal["extended", "core_repair"]
    status: Literal["draft", "active", "retired"]
    student_facing_language: str
    metacognition_prompt: str | None
    transfer_variation_of: str | None
    source_reference: dict
    exam_board: str
    syllabus_code: str
    tier_target: str
    paper_codes: list[str]
    syllabus_refs: list[str]
    source_style: str
    year10_sequence_band: str
    transfer_axis: list[str]
    problem_text: str
    student_prompt: str
    expected_answer: str
    marks: int
    difficulty: int
    calculator_policy: str
    notation_style: str
    concept_ids: list[str]
    exam_literacy_ids: list[str]
    prerequisite_ids: list[str]
    error_category_mapping: list[ErrorMappingView]
    hint_ladder: list[HintRung]
    expected_solution_steps: list[SolutionStepView]
    accepted_alternative_paths: list
    mark_scheme_notes: str
    examiner_report_notes: str


class AttemptHistoryView(BaseModel):
    id: int
    item_id: str
    track: Literal["core", "repair", "explore", "stretch", "review"]
    correct: bool
    hint_level_used: int
    attempted_at: datetime
    error_category: str | None
    diagnostic_target: str | None
    diagnostic_sentence: str | None
    repair_node_ids: list[str]
    path_match_status: Literal["matched", "alternative", "unmatched", "n/a"]


class AttemptHistoryListResponse(BaseModel):
    attempts: list[AttemptHistoryView]


class WeaknessReportOperatorView(BaseModel):
    generated_at: datetime
    window_days: int
    attempts_count: int
    correct_count: int
    top_error_category: str | None
    top_repair_node_id: str | None
    stuck_point_sentence: str
    support_action_operator: str
    support_action_parent: str


class UnmatchedPathView(BaseModel):
    attempt_id: int
    item_id: str
    item_title: str
    attempted_at: datetime
    submitted_steps: list[str]


class UnmatchedPathsResponse(BaseModel):
    unmatched: list[UnmatchedPathView]


class ItemBankReloadResponse(BaseModel):
    reloaded_at: datetime
    item_bank: dict[str, int]


class ParentWeeklySummaryView(BaseModel):
    week_start: date
    week_end: date
    improving: str
    still_developing: str
    one_thing_that_would_help: str
    draft_status: Literal["unsent", "sent"]
    sent_at: datetime | None = None


class ParentSummarySentRequest(BaseModel):
    sent_at: datetime | None = None


class ParentSummarySentView(BaseModel):
    week_start: date
    week_end: date
    draft_status: Literal["sent"]
    sent_at: datetime
