from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


Tier = Literal["extended", "core_repair"]
NodeType = Literal["math_concept", "exam_literacy"]
NotationStyle = Literal[
    "igcse_standard",
    "edexcel_standard",
    "factorised_form",
    "expanded_form",
    "completed_square_form",
]
CalculatorPolicy = Literal["calculator_allowed", "non_calculator", "either"]
ExamBoard = Literal["edexcel_igcse_math_a"]
SyllabusCode = Literal["4MA1"]
TierTarget = Literal["higher", "foundation_prerequisite_repair"]
PaperCode = Literal["4MA1/1H", "4MA1/2H"]
SourceStyle = Literal["edexcel_style_original"]
Year10SequenceBand = Literal["prerequisite_repair", "core_target", "transfer", "stretch"]
TransferAxis = Literal[
    "wording_change",
    "sign_change",
    "form_change",
    "context_change",
    "representation_change",
    "method_choice",
    "introductory",
]
ErrorCategory = Literal[
    "calculation_error",
    "sign_error",
    "formula_memory_error",
    "conceptual_misunderstanding",
    "problem_interpretation_error",
    "strategy_selection_error",
    "checking_finalization_error",
    "time_pressure_error",
]


class SourceReference(BaseModel):
    source_type: Literal["edexcel_style_original", "official_reference", "terry_provided_pdf"]
    source_id: str
    notes: str


class Hint(BaseModel):
    level: Literal[1, 2, 3, 4]
    title: str
    prompt: str

    @field_validator("title", "prompt")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("hint text cannot be blank")
        return value


class SolutionStep(BaseModel):
    step_number: int = Field(ge=1)
    action: str
    expression: str
    diagnostic_target: str
    common_errors: list[str] = Field(min_length=1)
    diagnostic_sentence: str

    @field_validator("action", "expression", "diagnostic_target", "diagnostic_sentence")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("solution step fields cannot be blank")
        return value


class SolutionPath(BaseModel):
    path_id: str
    label: str
    steps: list[SolutionStep] = Field(min_length=1)

    @model_validator(mode="after")
    def _step_numbers_are_ordered(self) -> "SolutionPath":
        numbers = [step.step_number for step in self.steps]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("solution path step_number values must start at 1 and be consecutive")
        return self


class ErrorMappingEntry(BaseModel):
    code: str
    category: ErrorCategory
    trigger: str
    expected_step_number: int = Field(ge=1)
    diagnostic_target: str
    diagnostic_sentence: str
    repair_node_ids: list[str] = Field(min_length=1)

    @field_validator("code", "trigger", "diagnostic_target", "diagnostic_sentence")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("error mapping fields cannot be blank")
        return value


class Item(BaseModel):
    id: str
    title: str
    tier: Tier
    status: Literal["draft", "active", "retired"] = "draft"
    student_facing_language: Literal["en"] = "en"
    metacognition_prompt: str | None = None
    transfer_variation_of: str | None = None
    source_reference: SourceReference
    exam_board: ExamBoard
    syllabus_code: SyllabusCode
    tier_target: TierTarget
    paper_codes: list[PaperCode] = Field(min_length=1)
    syllabus_refs: list[str] = Field(min_length=1)
    source_style: SourceStyle
    year10_sequence_band: Year10SequenceBand
    transfer_axis: list[TransferAxis] = Field(min_length=1)
    problem_text: str
    student_prompt: str
    expected_answer: str
    marks: int = Field(ge=1, le=10)
    difficulty: int = Field(ge=1, le=5)
    calculator_policy: CalculatorPolicy
    notation_style: NotationStyle
    concept_ids: list[str] = Field(min_length=1)
    exam_literacy_ids: list[str] = Field(min_length=1)
    prerequisite_ids: list[str] = Field(default_factory=list)
    error_category_mapping: list[ErrorMappingEntry] = Field(min_length=1)
    hint_ladder: list[Hint] = Field(min_length=4, max_length=4)
    expected_solution_steps: list[SolutionStep] = Field(min_length=1)
    accepted_alternative_paths: list[SolutionPath] = Field(default_factory=list)
    mark_scheme_notes: str
    examiner_report_notes: str

    @field_validator("id", "title", "problem_text", "student_prompt", "expected_answer")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("required text fields cannot be blank")
        return value

    @field_validator("hint_ladder")
    @classmethod
    def _hint_levels_are_1_to_4(cls, value: list[Hint]) -> list[Hint]:
        levels = [hint.level for hint in value]
        if levels != [1, 2, 3, 4]:
            raise ValueError("hint_ladder must contain levels 1, 2, 3, and 4 in order")
        return value

    @model_validator(mode="after")
    def _quality_gate_consistency(self) -> "Item":
        if self.tier == "extended" and not self.prerequisite_ids:
            raise ValueError("extended items must include at least one prerequisite_id")
        step_numbers = {step.step_number for step in self.expected_solution_steps}
        for mapping in self.error_category_mapping:
            if mapping.expected_step_number not in step_numbers:
                raise ValueError(
                    f"error mapping {mapping.code!r} references missing step "
                    f"{mapping.expected_step_number}"
                )
        expected_numbers = [step.step_number for step in self.expected_solution_steps]
        if expected_numbers != list(range(1, len(expected_numbers) + 1)):
            raise ValueError("expected_solution_steps must start at 1 and be consecutive")
        return self

    def quality_gate(self) -> dict[str, Any]:
        required = {
            "concept_ids": bool(self.concept_ids),
            "exam_literacy_ids": bool(self.exam_literacy_ids),
            "prerequisite_ids": self.tier == "core_repair" or bool(self.prerequisite_ids),
            "error_category_mapping": bool(self.error_category_mapping),
            "hint_ladder": len(self.hint_ladder) == 4,
            "expected_solution_steps": bool(self.expected_solution_steps),
        }
        missing = [name for name, ok in required.items() if not ok]
        return {"passed": not missing, "missing": missing}

    def validate_against_graph(self, graph: "ConceptGraph") -> None:
        graph.validate_item_refs(self)


class GraphNode(BaseModel):
    id: str
    type: NodeType
    tier: Tier
    strand: str
    name_en: str
    name_ko_optional: str | None = None
    description: str
    prerequisites: list[str]
    diagnostic_focus: list[ErrorCategory]


class ConceptGraph(BaseModel):
    nodes: list[GraphNode]

    @property
    def node_ids(self) -> set[str]:
        return {node.id for node in self.nodes}

    @property
    def math_ids(self) -> set[str]:
        return {node.id for node in self.nodes if node.type == "math_concept"}

    @property
    def exam_ids(self) -> set[str]:
        return {node.id for node in self.nodes if node.type == "exam_literacy"}

    def validate_item_refs(self, item: Item) -> None:
        checks = {
            "concept_ids": (item.concept_ids, self.math_ids),
            "prerequisite_ids": (item.prerequisite_ids, self.node_ids),
            "exam_literacy_ids": (item.exam_literacy_ids, self.exam_ids),
        }
        errors: list[str] = []
        for field_name, (values, allowed) in checks.items():
            missing = sorted(set(values) - allowed)
            if missing:
                errors.append(f"{field_name}: unknown ids {missing}")
        for mapping in item.error_category_mapping:
            missing_repairs = sorted(set(mapping.repair_node_ids) - self.node_ids)
            if missing_repairs:
                errors.append(f"{mapping.code}: unknown repair_node_ids {missing_repairs}")
        if errors:
            raise ValueError("; ".join(errors))


def load_item(path: str | Path) -> Item:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Item.model_validate(data)


def load_graph(path: str | Path) -> ConceptGraph:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ConceptGraph.model_validate(data)


def validate_item_file(item_path: str | Path, graph_path: str | Path | None = None) -> dict[str, Any]:
    item = load_item(item_path)
    result = item.quality_gate()
    if graph_path is not None:
        item.validate_against_graph(load_graph(graph_path))
    return {"item_id": item.id, **result}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate SUMIN STUDY item JSON files.")
    parser.add_argument("items", nargs="+", help="Item JSON files to validate")
    parser.add_argument("--graph", help="Path to concept_graph.json")
    args = parser.parse_args()

    failed = False
    for item_path in args.items:
        try:
            result = validate_item_file(item_path, args.graph)
            print(json.dumps(result, ensure_ascii=False))
        except (ValidationError, ValueError) as exc:
            failed = True
            print(json.dumps({"item_path": item_path, "passed": False, "error": str(exc)}, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
