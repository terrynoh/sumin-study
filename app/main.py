from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import CONCEPT_GRAPH_PATH, CONTENT_ROOT, DB_PATH
from app.routers import operator, parent, student_read, student_write, system
from backend.item_bank import ItemBank
from backend.item_bank_holder import ItemBankHolder
from backend.persistence import LearningStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    bank = ItemBank.from_directory_tree(CONTENT_ROOT)
    app.state.bank_holder = ItemBankHolder(bank)
    app.state.bank_loaded_at = datetime.now()
    app.state.store = LearningStore(DB_PATH)
    app.state.concept_graph = json.loads(CONCEPT_GRAPH_PATH.read_text(encoding="utf-8"))
    app.state.started_at = datetime.now()
    yield


app = FastAPI(title="SUMIN STUDY API", version="0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-Role", "X-Student-Id", "Content-Type"],
)


@app.exception_handler(HTTPException)
async def http_handler(request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        body = exc.detail
    else:
        body = {"error": {"code": "HTTP_ERROR", "message": str(exc.detail), "details": {}}}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": {"errors": exc.errors()},
            }
        },
    )


app.include_router(system.router)
app.include_router(student_read.router)
app.include_router(student_write.router)
app.include_router(operator.router)
app.include_router(parent.router)
