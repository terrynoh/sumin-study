# SUMIN STUDY — API Specification v0.1 (draft)

> Source of truth: `MVP_SPEC.md` + `docs/DESIGN_BRIEF.md` v1.5.
> Backend implementation reference: `backend/` modules already validated.
>
> Version: v0.1 (2026-05-04) — initial draft for codex implementation + frontend wiring.
> Status: API core implemented through 001D. Backend gaps plus student, operator, and parent v1 endpoints are implemented.

---

## 1. Purpose

This document defines the HTTP API surface between the React + Vite frontend
and the Python backend (`backend/` modules). It covers v1 scope only;
future endpoints (v1.5+) are listed but not specified.

## 2. Stack and Conventions

- **Framework:** FastAPI (Python 3.11+, async-capable)
- **Serialization:** Pydantic v2 (already used in `schema/`)
- **Persistence:** SQLite via existing `LearningStore`
- **Item bank:** loaded once at app startup via `ItemBank.from_directory_tree(...)`,
  rebuilt on operator-triggered reload
- **Base URL:** `http://localhost:8000` (local-first desktop app)
- **Content-Type:** `application/json`
- **Date format:** ISO 8601 in UTC for timestamps; `YYYY-MM-DD` for dates
- **Identifiers:** `item_id` matches existing schema (`Q-NNN`, `CR-NNN`)

### 2.1 Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created (POST /attempts, POST /reflections) |
| 400 | Validation error (malformed request) |
| 403 | Role mismatch (X-Role header) |
| 404 | Resource not found (item_id, attempt_id) |
| 409 | Conflict (e.g. attempt submitted with stale repair_context) |
| 500 | Server error |

### 2.2 Error Envelope

All non-2xx responses use:

```json
{
  "error": {
    "code": "ITEM_NOT_FOUND",
    "message": "Item Q-099 not found in active bank.",
    "details": {}
  }
}
```

## 3. Authentication and Roles

v1 is a local-first single-student desktop app. No login.

- `X-Student-Id` header: hardcoded `"sumin"` for v1. Reserved for future multi-student.
- `X-Role` header: `"student"` | `"operator"` | `"parent"`. Required on every request.
  - Mismatch with endpoint role requirement → 403
- Operator-only endpoints prefix: `/operator/...`
- Parent-only endpoints prefix: `/parent/...`
- Student endpoints have no prefix

v1.5+ may add OS-level role gating (separate desktop launcher icons) but the
header contract stays.

## 4. Domain Models (response/request shapes)

All models are Pydantic v2. Names mirror `backend/models.py` and `schema/`
where possible. Student-facing models strip operator-only fields.

### 4.1 ItemForStudent (response)

Fields exposed to the student. Excludes solution-revealing data.

```python
class ItemForStudent:
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
    hint_ladder: list[HintRung]   # title + prompt only
```

Tier semantics for v1:

- `extended` = Pearson Edexcel International GCSE Mathematics A 4MA1 Higher target item.
- `core_repair` = Foundation-assumed prerequisite repair item for the Higher path.

Excluded from student view: `expected_answer`, `expected_solution_steps`,
`error_category_mapping`, `accepted_alternative_paths`, `mark_scheme_notes`,
`examiner_report_notes`, `source_reference`, `concept_ids`, `prerequisite_ids`,
`exam_literacy_ids`, `transfer_variation_of`, `status`, `exam_board`,
`syllabus_code`, `tier_target`, `paper_codes`, `syllabus_refs`,
`source_style`, `year10_sequence_band`, `transfer_axis`.

### 4.2 ItemForOperator (response)

Full item including all schema fields. Returned only on `/operator/items/{id}`.

Additional Edexcel alignment fields:

```python
exam_board: str                 # edexcel_igcse_math_a
syllabus_code: str              # 4MA1
tier_target: str                # higher | foundation_prerequisite_repair
paper_codes: list[str]          # 4MA1/1H, 4MA1/2H
syllabus_refs: list[str]
source_style: str               # edexcel_style_original
year10_sequence_band: str       # prerequisite_repair | core_target | transfer | stretch
transfer_axis: list[str]
```

### 4.3 SessionTaskView

```python
class SessionTaskView:
    track: Literal["core", "repair", "explore", "stretch", "review"]
    item_id: str
    item_title: str
    reason: str
    locked: bool
```

Mirrors `SessionTask` but adds `item_title` for display convenience.

### 4.4 DailySessionPlanView

```python
class DailySessionPlanView:
    student_id: str
    session_date: date
    tasks: list[SessionTaskView]      # already in Core->Review->Repair->Explore->Stretch order
    notes: list[str]
```

### 4.5 MasteryVectorView

```python
class MasteryVectorView:
    concept_id: str
    concept_name_en: str               # joined from concept_graph
    accuracy: Literal["ready", "developing", "not_checked"]
    hint_independence: ...
    retention: ...
    transfer: ...
    articulation: ...
    mastered: bool
```

### 4.6 AttemptSubmitRequest

```python
class AttemptSubmitRequest:
    item_id: str
    track: Literal["core", "repair", "explore", "stretch", "review"]
    submitted_answer: str
    submitted_steps: list[str] = []
    hint_level_used: int = 0           # 0..4
    selected_error_code: str | None = None
    articulation_ok: bool | None = None
    repair_context: RepairContextDTO | None = None
```

### 4.7 RepairContextDTO

```python
class RepairContextDTO:
    original_item_id: str
    original_track: Literal[...]
    repair_chain: list[str]
    depth: int
    escalated: bool
```

Matches `backend.models.RepairContext` 1:1.

### 4.8 AttemptOutcomeView (response)

```python
class AttemptOutcomeView:
    attempt_id: int                    # SQLite row id (NEW: requires persistence change, see §10)
    item_id: str
    correct: bool
    feedback: str                      # AnswerCheckResult.feedback
    selected_error_code: str | None
    stuck_point: StuckPointView | None
    step_checks: list[StepCheckView]
    next_item_id: str                  # from AttemptService.next_item_after
    next_track: Literal[...]
    repair_context_after: RepairContextDTO | None
    mastery_vectors: list[MasteryVectorView]    # affected concepts only
```

### 4.9 StuckPointView

```python
class StuckPointView:
    matched: bool
    error_code: str | None
    category: str | None
    diagnostic_sentence: str
    repair_node_ids: list[str]
    fallback: bool
```

Mirrors `StuckPointMatch` minus internal `confidence` field (operator-only).

### 4.10 WeaknessReportView (operator/parent variants)

**Operator (`/operator/weakness-report`):** full WeaknessReport including
`support_action_operator` and raw aggregates.

**Parent (`/parent/weekly-summary`):** strips `support_action_operator`,
`top_repair_node_id`, raw counts. Keeps `stuck_point_sentence` and
`support_action_parent` only.

## 5. Student Endpoints

### 5.1 GET /session/today

Returns today's `DailySessionPlanView`.

- Params: `?date=YYYY-MM-DD` (optional, defaults to server today)
- Computes `build_daily_plan(student_id, session_date, attempts)` via SessionEngine
- Tasks already in Core→Review→Repair→Explore→Stretch order
- Locked tasks include `locked: true` flag (frontend disables interaction)

### 5.2 GET /items/{item_id}

Returns `ItemForStudent` for the given id.

- 404 if item missing or `status != "active"`
- Tier-blind: returns Extended or CR depending on requested id

### 5.3 POST /attempts

Request body: `AttemptSubmitRequest`.

Response: `AttemptOutcomeView` (201).

- Calls `AttemptService.submit(...)` then `next_item_after(...)` and packs both into one response
- `mastery_vectors` includes only concepts in the submitted item's `concept_ids` (not full snapshot)
- Errors:
  - 404 if `item_id` unknown
  - 400 if `track` is `"repair"` but `repair_context` is null (or vice versa)
  - 409 if `repair_context.original_item_id` does not exist

### 5.4 GET /mastery

Returns full mastery snapshot for the student.

```json
{
  "student_id": "sumin",
  "vectors": [MasteryVectorView, ...],
  "generated_at": "2026-05-04T12:00:00Z"
}
```

- Only concepts with at least one attempt are returned (not all graph nodes)
- For Progress screen (§4.8 in DESIGN_BRIEF)

### 5.5 GET /retention/due

Returns due retention reviews. Mirrors `due_retention_reviews(...)`.

Used by Review Queue screen (§4.6). Same data is also embedded in
`/session/today.tasks` filtered to `track == "review"`.

### 5.6 POST /reflections

Request:

```json
{
  "item_id": "Q-001",
  "reflection_text": "Because finding two numbers...",
  "articulation_ok": true
}
```

- v1: stores reflection text + boolean. Articulation scoring is rule-based
  (keyword match against expected explanation tokens — see DESIGN_BRIEF §8).
- Reflection text NOT exposed via Operator API (per DESIGN_BRIEF §10 whitelist).
- Response 201 with `{"stored": true}`.

**Persistence note:** requires new `reflections` table. See §10.

### 5.7 GET /weakness-report (student-facing variant)

Returns `stuck_point_sentence` + per-concept `MasteryVectorView` for the
Progress screen. Excludes `support_action_*` fields.

## 6. Operator Endpoints

All require `X-Role: operator`.

### 6.1 GET /operator/items

Returns full item bank with quality-gate status.

The `tier` values keep their v1 API names for compatibility. Interpret
`extended` as a 4MA1 Higher target item and `core_repair` as
Foundation-assumed prerequisite repair.

```json
{
  "items": [
    {
      "id": "Q-001",
      "tier": "extended",
      "status": "active",
      "concept_ids": [...],
      "gates": {
        "concept_ids": "ok",
        "exam_literacy_ids": "ok",
        "prerequisite_ids": "ok",
        "error_category_mapping": "ok",
        "hint_ladder": "ok",
        "expected_solution_steps": "ok"
      },
      "attempt_count": 7,
      "correct_ratio": 0.71,
      "avg_hint_level": 1.8
    }
  ]
}
```

Gate fields use existing schema validation. Non-passing items show specific
failing field name (DESIGN_BRIEF §4.10 B3 decision).

### 6.2 GET /operator/items/{item_id}

Returns full `ItemForOperator` (all schema fields).

### 6.3 GET /operator/attempts

Query params:
- `?since=YYYY-MM-DD` (default: 14 days ago)
- `?limit=100` (max 500)

Returns whitelisted attempt records:

```json
{
  "attempts": [
    {
      "id": 47,
      "item_id": "Q-005",
      "track": "core",
      "correct": false,
      "hint_level_used": 2,
      "attempted_at": "2026-05-03T18:30:00Z",
      "error_category": "checking_finalization_error",
      "diagnostic_target": "solve_after_factorising",
      "diagnostic_sentence": "...",
      "repair_node_ids": [...]
    }
  ]
}
```

Excluded per DESIGN_BRIEF §10: `submitted_steps verbatim`, `reflection_text
verbatim`, `metacognition_input verbatim`. These need a separate "Deep dive"
endpoint with explicit confirmation — deferred to v1.5.

### 6.4 GET /operator/weakness-report

Query params:
- `?window_days=14` (default)
- `?as_of=YYYY-MM-DD` (default: today)

Returns full operator-variant `WeaknessReportView`.

### 6.5 GET /operator/unmatched-paths

Returns attempts where the student's submitted_steps did not match either
expected path or any accepted_alternative_path but produced a correct answer.

```json
{
  "unmatched": [
    {
      "attempt_id": 12,
      "item_id": "Q-001",
      "submitted_steps": ["...", "..."],
      "attempted_at": "2026-05-03T..."
    }
  ]
}
```

Contract-audit update (2026-05-03): `submitted_steps` are exposed here only
for operator review of unmatched successful paths. `submitted_answer` remains
excluded. The backend now implements `path_match_status` and persisted
unmatched submitted steps; the original backend-gap note below is historical.

**Backend gap:** current `attempt_service` does not flag unmatched-but-correct
attempts. Requires:
1. New persistence column `path_match_status` (matched | alternative | unmatched)
2. `attempt_service.submit` to set this based on `step_checker` results

See §10.

### 6.6 POST /operator/items/{item_id}/alternative-paths

Approve an unmatched path as a valid alternative.

Request:

```json
{
  "attempt_id": 12,
  "description": "Vieta's formulas approach",
  "step_pattern": ["sum=...", "product=...", "..."]
}
```

- Appends to the item's `accepted_alternative_paths` JSON file on disk
- Triggers item bank reload
- Future submissions matching this pattern → marked `alternative` instead of `unmatched`

**Backend gap:** alternative-path matching logic not yet implemented in
`step_checker`. Defer to v1.5 if pre-API timeline tight.

### 6.7 POST /operator/item-bank/reload

Forces `ItemBank.from_directory_tree(...)` re-read. No request body.

Use case: terry edits a CR JSON in editor, wants change visible without restart.

## 7. Parent Endpoints

All require `X-Role: parent`.

### 7.1 GET /parent/weekly-summary

Returns parent-variant `WeaknessReportView`:

```json
{
  "week_start": "2026-04-28",
  "week_end": "2026-05-04",
  "improving": "...",
  "still_developing": "...",
  "one_thing_that_would_help": "...",
  "draft_status": "unsent" | "sent"
}
```

v1 generates from template (`SUPPORT_ACTIONS` in `weakness_report.py`).
v2 will use LLM (DESIGN_BRIEF §17).

### 7.2 POST /parent/weekly-summary/sent

Marks the current week's summary as sent (operator confirms manual delivery).

Request: empty body or `{"sent_at": "..."}`.

**Persistence note:** requires new `parent_summaries` table or status column.
See §10.

## 8. System Endpoints

### 8.1 GET /health

Returns server health + bank stats:

```json
{
  "status": "ok",
  "item_bank": {"extended": 20, "core_repair": 25, "loaded_at": "..."},
  "db_path": "data/local/study.sqlite",
  "uptime_seconds": 1234
}
```

### 8.2 GET /concept-graph

Returns the concept graph for frontend display (used in Mastery screen labels).

Response: contents of `content/quadratics/concept_graph.json` directly.

## 9. Backend Module Mapping

| Endpoint | Backend call |
|---|---|
| GET /session/today | `LearningStore.list_attempts` + `SessionEngine.build_daily_plan` |
| GET /items/{id} | `ItemBank.get` + filter to `ItemForStudent` |
| POST /attempts | `AttemptService.submit` + `next_item_after` |
| GET /mastery | `LearningStore.list_attempts` + `mastery.calculate_mastery_vectors` |
| GET /retention/due | `LearningStore.list_attempts` + `retention.due_retention_reviews` |
| POST /reflections | NEW: `LearningStore.add_reflection` (§10) |
| GET /weakness-report | `weakness_report.build_weakness_report` (filtered for student) |
| GET /operator/items | `ItemBank.all` + per-item attempt aggregation |
| GET /operator/items/{id} | `ItemBank.get` (full) |
| GET /operator/attempts | `LearningStore.list_attempts` (whitelist filter) |
| GET /operator/weakness-report | `weakness_report.build_weakness_report` (operator variant) |
| GET /operator/unmatched-paths | NEW: `LearningStore.list_unmatched_paths` (§10) |
| POST /operator/items/{id}/alternative-paths | NEW: file write + item bank reload |
| POST /operator/item-bank/reload | `ItemBank.from_directory_tree` (re-init) |
| GET /parent/weekly-summary | `weakness_report.build_weakness_report` (parent variant) |
| POST /parent/weekly-summary/sent | NEW: `LearningStore.mark_summary_sent` (§10) |
| GET /health | trivial |
| GET /concept-graph | file read |

## 10. Backend Gaps Required for This API

Contract-audit update (2026-05-03): G1-G5 are implemented in backend. Parent
HTTP endpoints are implemented in PHASE3-API-001D. Reflection storage now also
updates the latest matching attempt's `articulation_ok` when supplied, so
mastery vectors reflect post-attempt articulation.

Before implementation starts, the following backend changes are needed.
These are **out of scope for the API task itself** but blocking dependencies:

### G1. AttemptRecord exposes `id`

Currently `AttemptRecord` is identifier-less from the persistence side
(SQLite has autoincrement id but `LearningStore.list_attempts` does not
return it). Frontend needs `attempt_id` to reference attempts in operator
workflow.

**Change:** add `id: int | None = None` to `AttemptRecord` and select it in
`list_attempts`.

### G2. Path match status

For `/operator/unmatched-paths`. Add column + `attempt_service` logic to
classify each correct attempt as `matched | alternative | unmatched`.

### G3. Reflections table

For `/reflections` POST. Schema:

```sql
CREATE TABLE reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    reflection_text TEXT NOT NULL,
    articulation_ok INTEGER,
    submitted_at TEXT NOT NULL
);
```

Not exposed via operator endpoints (whitelist).

### G4. Parent summaries table

For `/parent/weekly-summary/sent` status tracking:

```sql
CREATE TABLE parent_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,
    draft_text TEXT NOT NULL,
    sent_at TEXT
);
```

### G5. Item bank reload thread-safety

`ItemBank` is held as a singleton. POST `/operator/item-bank/reload` needs
either (a) atomic swap with a lock, or (b) FastAPI lifespan-style restart.

## 11. v1.5 Deferred Endpoints

Not included in v1 implementation:

- `GET /operator/deep-dive/attempts/{id}` — verbatim reflection/metacognition
  text (requires per-session explicit confirmation)
- `POST /attempts/{id}/articulation-rescore` — LLM rescoring
- `WebSocket /session/live` — real-time multi-device sync
- `POST /system/migrate` — v2 schema migration
- LLM-driven endpoints (parent summary draft, dynamic stuck-point messages)

## 12. Implementation Order

Recommended for codex when this brief is dispatched:

1. **G1 + G2 + G3 + G4 backend gaps** (1 brief)
2. **System + read-only student endpoints**: /health, /concept-graph,
   /items/{id}, /session/today, /mastery, /retention/due, /weakness-report
3. **POST /attempts + POST /reflections** (the write path)
4. **Operator read endpoints**: /operator/items, /operator/attempts,
   /operator/weakness-report, /operator/unmatched-paths
5. **Operator write endpoints**: /operator/items/{id}/alternative-paths,
   /operator/item-bank/reload
6. **Parent endpoints**: /parent/weekly-summary, /parent/weekly-summary/sent
7. **Smoke test**: full Core session flow via API end-to-end (replaces
   `tools/session_smoke.py` with HTTP smoke)

## 13. Open Questions for Terry

Contract-audit update (2026-05-03): resolved defaults are CORS
`http://localhost:5173`, DB env override via `SUMIN_STUDY_DB_PATH`, local
`X-Role` gating, reflection text stored but not operator-exposed, and parent
summary generated on demand.

1. **CORS:** local-first desktop app likely embeds frontend in same origin
   (Tauri or pywebview), so CORS may not be needed. If frontend dev server
   runs separately on port 5173, CORS allowlist needed.

2. **DB path:** v1 default `data/local/study.sqlite`. Production student PC
   may want a user-chosen path (e.g. OneDrive sync). Configurable via
   env var `SUMIN_STUDY_DB_PATH`?

3. **Operator/parent role gating:** v1 uses simple header. Anyone can
   forge the header. Acceptable for single-user local app, or stricter
   needed (e.g. per-launch role lock)?

4. **Reflection text storage policy:** v1 stores verbatim in DB but never
   exposes via operator API. Confirm: storing is OK (for future articulation
   re-scoring), exposing is forbidden?

5. **Parent summary frequency:** weekly assumed. Generated on-demand via GET,
   or pre-generated weekly cron-style? v1 simplest = on-demand.

## Changelog

- **v0.1-contract-audit (2026-05-03)** — Updated implementation status,
  unmatched-path privacy note, backend gap status, and resolved defaults.
- **v0.1-001D (2026-05-03)** — Parent weekly summary endpoints implemented;
  parent response remains privacy-stripped and on-demand generated.
- **v0.1 (2026-05-04)** — Initial draft. Endpoints, models, backend mapping,
  required backend gaps, implementation order, open questions.
