from __future__ import annotations

from collections.abc import Callable

from fastapi import Header, HTTPException, Request

from backend.item_bank import ItemBank
from backend.persistence import LearningStore


def get_bank(request: Request) -> ItemBank:
    return request.app.state.bank_holder.current()


def get_store(request: Request) -> LearningStore:
    return request.app.state.store


def get_concept_graph(request: Request) -> dict:
    return request.app.state.concept_graph


def require_role(required: str) -> Callable:
    def _dep(
        x_role: str = Header(..., alias="X-Role"),
        x_student_id: str = Header("sumin", alias="X-Student-Id"),
    ) -> str:
        if x_role != required:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "ROLE_MISMATCH",
                        "message": f"required {required}",
                        "details": {"received": x_role},
                    }
                },
            )
        return x_student_id

    return _dep


require_student = require_role("student")
require_operator = require_role("operator")
require_parent = require_role("parent")
