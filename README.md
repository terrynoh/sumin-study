# SUMIN STUDY

Local-first self-study app for a Year 10 student preparing for Pearson Edexcel
International GCSE Mathematics A 4MA1 Higher.

The v1 MVP focuses on quadratics. It is designed to help the student notice
where mathematical thinking breaks, repair that link, and transfer the repaired
understanding into exam-style problems.

## Current v1 Scope

- 20 Edexcel 4MA1 Higher quadratics target items
- 25 prerequisite repair items
- React + Vite student UI
- FastAPI backend
- Local SQLite learning store
- Hidden operator view at `/?view=operator`
- No LLM in the v1 student loop
- Local desktop launch through PowerShell scripts and Windows shortcuts

## First Run

Install Python and Node.js on the machine, then from this repository:

```powershell
pip install -r requirements.txt
cd frontend
npm.cmd install
npm.cmd run build
cd ..
scripts\create_shortcuts.ps1
```

Student launcher:

```powershell
scripts\start_local.ps1
```

Operator launcher:

```powershell
scripts\start_local.ps1 -View operator
```

Stop local services:

```powershell
scripts\stop_local.ps1
```

## Data

Student learning data is local and intentionally not committed.

Default path:

```text
data/local/study.sqlite
```

## Canonical Docs

- `MVP_SPEC.md`
- `docs/DESIGN_BRIEF.md`
- `docs/EDEXCEL_4MA1_ALIGNMENT_AUDIT.md`
- `docs/EDEXCEL_ITEM_QUALITY_REVIEW.md`
- `_agents/NEXT_SESSION_HANDOFF.md`
