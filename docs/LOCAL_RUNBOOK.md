# SUMIN STUDY Local Runbook

## Scope

v1 is a local-first desktop web app. The student PC runs the API, the built
React frontend, and the SQLite database locally. No cloud sync, account login,
or external LLM call is required for the v1 student loop.

## Confirmed v1 Pilot Packaging

Use a PowerShell launcher internally, wrapped by Windows shortcuts for the
student/operator experience.

Rationale:

- The current product risk is learning-loop quality, not installer polish.
- A PowerShell launcher is transparent and easy to debug on Terry's PC.
- The student should not need to see or type PowerShell commands.
- Desktop shortcuts make the pilot feel app-like without hiding the moving
  parts too early.
- An exe/Tauri wrapper can come later once ports, DB location, and role entry
  points are stable.

## Build PC Flow

From `frontend/`:

```powershell
npm.cmd run build
```

Then copy the project folder to the student desktop or package it with the
Python runtime, frontend `dist/`, content files, and `data/local/`.

## Student PC Shortcut UX

Create shortcuts from the project root:

```powershell
scripts\create_shortcuts.ps1
```

This creates:

- `SUMIN STUDY`: opens the student view.
- `SUMIN STUDY Operator`: opens the operator view.
- `Stop SUMIN STUDY`: stops local services.

Student-facing behaviour:

- Sumin double-clicks `SUMIN STUDY`.
- The API and local web app start in the background.
- The browser opens to the student session.
- No API, port, database, or command-line detail is part of the student flow.

Operator-facing behaviour:

- Terry double-clicks `SUMIN STUDY Operator`.
- The browser opens to `/?view=operator`.
- Operator tools stay separate from the student learning flow.

## Manual Start

Student view:

```powershell
scripts\start_local.ps1
```

Operator view:

```powershell
scripts\start_local.ps1 -View operator
```

Add `-NoBrowser` when starting services without opening a browser.

## Stop

```powershell
scripts\stop_local.ps1
```

## Data Location

Default SQLite path:

```text
data/local/study.sqlite
```

Optional override:

```powershell
scripts\start_local.ps1 -DbPath "C:\Path\To\study.sqlite"
```

## Next Packaging Decision

Decision before moving beyond this launcher:

- keep PowerShell launcher plus Windows shortcuts for v1 pilot,
- then consider an exe wrapper with Tauri/pywebview after student-loop usage
  is stable.

The exe path should wait until student-loop usage proves the local app shape is
stable.
