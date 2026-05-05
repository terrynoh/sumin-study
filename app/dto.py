from __future__ import annotations

from datetime import datetime

from app.schemas import MasteryVectorView, RepairContextDTO
from backend.models import RepairContext, Track


def to_repair_context(dto: RepairContextDTO | None) -> RepairContext | None:
    if dto is None:
        return None
    return RepairContext(
        original_item_id=dto.original_item_id,
        original_track=Track(dto.original_track),
        repair_chain=tuple(dto.repair_chain),
        depth=dto.depth,
        escalated=dto.escalated,
    )


def from_repair_context(ctx: RepairContext | None) -> RepairContextDTO | None:
    if ctx is None:
        return None
    return RepairContextDTO(
        original_item_id=ctx.original_item_id,
        original_track=ctx.original_track.value,
        repair_chain=list(ctx.repair_chain),
        depth=ctx.depth,
        escalated=ctx.escalated,
    )


def vector_views(vectors, graph: dict, *, concept_ids: set[str] | None = None) -> list[MasteryVectorView]:
    names = {node["id"]: node.get("name_en", node["id"]) for node in graph.get("nodes", [])}
    selected = vectors.items()
    if concept_ids is not None:
        selected = [(concept_id, vector) for concept_id, vector in selected if concept_id in concept_ids]
    return [
        MasteryVectorView(
            concept_id=concept_id,
            concept_name_en=names.get(concept_id, concept_id),
            accuracy=vector.accuracy.value,
            hint_independence=vector.hint_independence.value,
            retention=vector.retention.value,
            transfer=vector.transfer.value,
            articulation=vector.articulation.value,
            mastered=vector.mastered,
        )
        for concept_id, vector in sorted(selected)
    ]
