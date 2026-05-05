# SUMIN STUDY - Next Session Handoff

Date: 2026-05-05

## Current Status

The project is at a v1 pilot-ready implementation checkpoint, pending the next
decision/review pass.

Target:
- Pearson Edexcel International GCSE Mathematics A 4MA1 Higher
- Year 10
- Topic: Quadratics MVP
- Student-facing language: English
- Deployment: local-first desktop web app
- v1 launch UX: PowerShell launcher behind Windows shortcuts

Core purpose remains:
1. Metacognitive control: Sumin notices where her thinking breaks.
2. Affective control: restore perceived control over effort -> result.
3. Performance transfer: improve real exam transfer, not just procedure recall.

## Canonical Files To Load First

1. `MVP_SPEC.md`
2. `docs/DESIGN_BRIEF.md`
3. `docs/EDEXCEL_4MA1_ALIGNMENT_AUDIT.md`
4. `docs/EDEXCEL_ITEM_QUALITY_REVIEW.md`
5. `_agents/inbox_for_codex.md` tail
6. `_agents/inbox_for_claude.md` tail

## Implemented

Backend/API:
- Student read/write endpoints complete.
- Operator endpoints complete.
- Parent weekly summary endpoints complete.
- Reflection updates articulation.
- Privacy boundaries intact: operator does not expose raw reflection text.

Frontend:
- React + Vite student loop works.
- Repair branch works and returns to original item.
- Reflection screen after 3 Core links works.
- Session End screen works.
- Hidden operator view at `/?view=operator` works.
- Parent Draft `Mark reviewed` is local-only and does not send externally.

Content:
- 20 Higher target items active.
- 25 prerequisite repair items active.
- Added after academic filter:
  - `CR-023`: double-bracket expansion, positive constants
  - `CR-024`: double-bracket expansion, mixed signs
  - `CR-025`: zero-product property
- Q-013 remains Stretch.
- Stretch items are excluded from automatic Core path.

Deployment:
- `scripts/start_local.ps1`
- `scripts/stop_local.ps1`
- `scripts/create_shortcuts.ps1`
- `docs/LOCAL_RUNBOOK.md`
- Shortcuts have not been created yet.
- Local services are not currently running.

## Latest Academic Filter Decisions

Accepted before v1 pilot:
- Add direct double-bracket repair.
- Add zero-product repair.
- Reword procedural metacognition prompts.
- Rework Q-013 trigger while keeping it Stretch.
- Reframe dashboard first message away from `wrong last time`.
- Mark Q-001 as introductory.

Deferred to v1.1:
- Accepted alternative solution paths.
- More error mappings for multi-step Stretch items.
- CR wording variety after observing repetition fatigue.
- `show that` / `hence` exam-literacy items.
- `routing_anchor_ids` separation from `prerequisite_ids`.

## Last Validation Passed

- `schema/item.py` validation for all 45 items
- `tools/edexcel_alignment_audit.py`
- `tools/item_language_audit.py`
- `tools/hint_audit.py`
- `tools/cr_polish_audit.py`
- `tools/repair_routing_audit.py`
- `tools/phase2_check.py`
- `tools/api_smoke_001a.py`
- `tools/api_smoke_001b.py`
- `tools/api_smoke_001c.py`
- `tools/api_smoke_001d.py`
- `tools/contract_audit.py`

Manual routing sample also passed:
- Q-003 / Q003_MIDDLE_TERM_MISSING -> CR-023
- Q-006 / Q006_MIDDLE_TERM_CHECK -> CR-023 first; CR-024 remains variation
- Q-005 / Q005_WRONG_ROOT_SIGNS -> CR-025

## Next Session Recommended Start

Start with one of these, depending on Terry's preference:

1. Run local pilot launch path:
   - build frontend
   - create shortcuts intentionally
   - start `SUMIN STUDY`
   - browser smoke student view and operator view

2. Do a final v1 pilot QA pass:
   - student flow from shortcut
   - repair branch
   - reflection
   - operator parent draft review

3. Prepare v1.1 backlog:
   - alternative paths
   - `show that` / `hence`
   - CR wording variety
   - `routing_anchor_ids`

## Important Boundaries

- Do not introduce LLM into the v1 student path.
- Do not let Claude own API/DB/schema/test contracts.
- Use Claude only for academic/curriculum/tone review when specifically useful.
- Do not create Desktop shortcuts or run local services without Terry's explicit next instruction.
