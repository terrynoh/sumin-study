from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Request

from app.config import CONCEPT_GRAPH_PATH
from app.schemas import HealthView


router = APIRouter()


@router.get("/health", response_model=HealthView)
def health(request: Request) -> HealthView:
    bank = request.app.state.bank_holder.current()
    started_at: datetime = request.app.state.started_at
    loaded_at: datetime = request.app.state.bank_loaded_at
    return HealthView(
        status="ok",
        item_bank={
            "extended": len(bank.by_tier("extended")),
            "core_repair": len(bank.by_tier("core_repair")),
            "loaded_at": loaded_at.isoformat(),
        },
        db_path=str(request.app.state.store.db_path),
        uptime_seconds=int((datetime.now() - started_at).total_seconds()),
    )


@router.get("/concept-graph")
def concept_graph(request: Request) -> dict:
    return request.app.state.concept_graph
