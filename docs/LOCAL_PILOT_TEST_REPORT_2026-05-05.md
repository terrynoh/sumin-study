# SUMIN STUDY Local Pilot Test Report

Date: 2026-05-05 19:21:22 +07:00  
Prepared for: next chat/session handoff  
Repository: `terrynoh/sumin-study`  
Local project path tested: `C:\SUMIN_STUDY`

## 1. Purpose

This report records the confirmed local computer environment, setup actions,
code fixes, launch status, and browser smoke test results for the SUMIN STUDY
v1 local pilot.

The goal is to let the next chat/session continue without rediscovering the
same environment and launch issues.

## 2. Machine and Runtime Environment

Confirmed environment:

- OS shell used: Windows PowerShell
- Local timezone during test: Asia/Bangkok, UTC+07:00
- Project folder: `C:\SUMIN_STUDY`
- Source origin: GitHub repository ZIP from `terrynoh/sumin-study`, default branch `main`
- Local folder was not originally a Git working tree because it was downloaded as ZIP.

Installed or prepared during this session:

- Python: `3.13.13`
- pip: `26.0.1`
- Node.js: `24.15.0`
- npm: `11.12.1`
- Git for Windows: `2.54.0.windows.1`
- Microsoft Edge executable confirmed at:
  `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`

Important Node detail:

- Node.js MSI system install failed because the account lacked all-user install
  privileges.
- Node.js MSI per-user install also failed while writing `corepack`.
- Resolution: official Node.js ZIP runtime was unpacked under:
  `C:\SUMIN_STUDY\.runtime\node-v24.15.0-win-x64`
- User PATH was updated so `npm.cmd` resolves from that project runtime.
- PowerShell may block plain `npm` because it resolves to `npm.ps1`.
  Use `npm.cmd` in PowerShell.

## 3. Dependency Setup

Backend dependencies installed successfully:

```powershell
python -m pip install -r requirements.txt
```

Frontend dependencies installed successfully:

```powershell
cd C:\SUMIN_STUDY\frontend
npm.cmd install
```

Frontend production build succeeded:

```powershell
$env:VITE_API_BASE='http://127.0.0.1:8000'
npm.cmd run build
```

Build output:

- `frontend/dist/index.html`
- built JS/CSS assets under `frontend/dist/assets`

## 4. Code Fixes Applied During Local Pilot

Two launch-blocking issues were found and fixed.

### 4.1 PowerShell shortcut/start script path type

Files:

- `scripts/create_shortcuts.ps1`
- `scripts/start_local.ps1`

Problem:

- `Resolve-Path` returns a `PathInfo` object.
- The shortcut COM object expected `WorkingDirectory` as a string.
- `start_local.ps1` also passed a `PathInfo` object into later path operations.

Fix:

- Use `.Path` from the resolved path.

### 4.2 API CORS for production preview port

File:

- `app/main.py`

Problem:

- Frontend preview runs on `http://127.0.0.1:4173`.
- API CORS only allowed Vite dev server origins `5173`.
- Browser smoke failed with frontend `Failed to fetch` even though API health was OK.

Fix:

- Added `http://localhost:4173` and `http://127.0.0.1:4173` to CORS allowed origins.

## 5. Desktop Shortcuts

Desktop shortcuts were created successfully in the Windows Desktop folder
returned by:

```powershell
[Environment]::GetFolderPath("Desktop")
```

Created shortcuts:

- `SUMIN STUDY.lnk`
- `SUMIN STUDY Operator.lnk`
- `Stop SUMIN STUDY.lnk`

The script uses one-time PowerShell execution policy bypass in the shortcut
arguments, matching the repository runbook pattern:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...
```

No persistent PowerShell execution policy weakening was applied.

## 6. Local Services

Local services were started successfully.

Confirmed URLs:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:4173`
- Student view: `http://127.0.0.1:4173`
- Operator view: `http://127.0.0.1:4173/?view=operator`

Confirmed API health response:

```json
{
  "status": "ok",
  "item_bank": {
    "extended": 20,
    "core_repair": 25
  },
  "db_path": "C:\\SUMIN_STUDY\\data\\local\\study.sqlite"
}
```

Ports confirmed listening:

- `127.0.0.1:8000`
- `127.0.0.1:4173`

## 7. Validation and Smoke Tests

The following checks passed after environment setup:

- frontend build: `npm.cmd run build`
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

Note:

- `tools/hint_audit.py` requires explicit item file arguments.
- In PowerShell, expand item files first and pass the list to Python.

## 8. Browser Smoke Test Result

Browser smoke was performed with Microsoft Edge through Playwright automation.

Reason:

- The in-app browser automation surface was not available in this session.
- Edge was present locally, so Playwright used the installed Edge executable.

Smoke test result: PASS

Student session verified:

- Student view loads.
- Session Plan loads.
- Core task opens.
- Hint ladder displays.
- Incorrect answer produces repair signal.
- Repair screen opens from feedback.

Operator view verified:

- Operator view loads.
- Item bank panel is visible.
- Weakness report panel is visible.
- Parent draft panel is visible.
- Operator item detail opens.
- Edexcel metadata and expected-answer fields are visible in item detail.

Smoke screenshots saved locally:

- `C:\SUMIN_STUDY\.tmp\student-smoke.png`
- `C:\SUMIN_STUDY\.tmp\operator-smoke.png`

These screenshots were not uploaded to GitHub because they are generated local
artifacts.

## 9. Important Local Artifacts Not To Commit

Do not commit these local/generated directories:

- `.installers`
- `.runtime`
- `.tmp`
- `data`
- `frontend/node_modules`
- `frontend/dist`

## 10. Current Known Good Launch Commands

From `C:\SUMIN_STUDY`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SUMIN_STUDY\scripts\start_local.ps1 -NoBrowser
```

Student browser URL:

```text
http://127.0.0.1:4173
```

Operator browser URL:

```text
http://127.0.0.1:4173/?view=operator
```

Stop command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\SUMIN_STUDY\scripts\stop_local.ps1
```

Safety note:

- `stop_local.ps1` stops processes listening on ports `8000`, `4173`, and
  `5173`.
- If other local services use those ports, confirm before running it.

## 11. Handoff Summary

The v1 local pilot launch path is now confirmed on this PC:

1. Required runtimes are installed or available.
2. Backend dependencies are installed.
3. Frontend dependencies are installed.
4. Production frontend build succeeds.
5. Desktop shortcuts are created.
6. Local API and frontend run.
7. Student and operator browser smoke tests pass.

Next recommended step:

- Run a manual human QA pass from the desktop shortcuts:
  `SUMIN STUDY`, `SUMIN STUDY Operator`, and `Stop SUMIN STUDY`.
