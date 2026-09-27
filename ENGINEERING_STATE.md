# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "M008 — User model + password hashing"
Completed milestones: ["M001", "M002", "M003", "M004", "M005", "M006", "M007"]
Current implementation status: "M007 done: GET /health (liveness, never touches DB) and GET /ready (SELECT 1 within 2s asyncio.wait_for timeout → 200/503) mounted at app root outside /api/v1; public but non-revealing, detail only in server logs. Verified live across DB stop/restart."
Known bugs: []
Known security issues: []
Known performance issues: []
Known resource/memory issues:
  - "Residual (documented, not reproducible locally): asyncio.wait_for cancelling /ready's check mid real-socket cleanup; SQLAlchemy pool handles greenlet cancellation — re-measure in M056. Refused-connection path asserted clean (checkedout()==0)."
Technical debt: []
Blocked tasks: []
Next milestone: "M008 — User model + password hashing"
Last verification: "M007 gate PASSED with live dev DB (port 65432): ruff format OK, ruff check OK, mypy 32 files OK, pytest 44 passed / 0 skipped. Live uvicorn: /health=200 & /ready=200 (DB up) → /health=200 & /ready=503 (DB stopped) → /ready=200 (DB restarted). bandit on src/api/health.py exit 0."
Last test result: "pytest = 44 passed (health 9, root 4, config 8, db 4, redact 3, errors 8, logging 4, migrations 2, smoke 2)"
```

## Checkpoint decisions (human-confirmed, 2026-09-26)

| # | Decision |
|---|---|
| D1 | Section 3 locked architecture — confirmed as-is |
| D2 | Dev commands → `uv run ruff|mypy|pytest` + `scripts/check.ps1` (no make/just on this Windows host) |
| D3 | Password hashing → `passlib[bcrypt]` + pin `bcrypt==4.0.1` (revisit in M055) |
| D4 | Authorized system actions: `git init`; start Docker Desktop when M003+ verification needs the dev Postgres |
| D5 | JWT library → **PyJWT** (Section 3 allows "python-jose or pyjwt") |
| D6 | Python → **3.12** pinned via `.python-version` / `requires-python` |

## Milestone commits

| Milestone | Commit |
|---|---|
| M000 (kickoff) | `11de9f6` |
| M001 | `ddaf68f` |
| M002 | `d62d934` |
| M003 | `9eaaec2` |
| M004 | `2349f44` |
| M005 | `4cf0a5e` |
| M006 | `d303bb0` |
| M007 | `<pending — recorded after commit>` |

## Notes / findings

- 2026-09-27: `MILESTONES.md` repaired. A PowerShell 5.1 `Add-Content` (ANSI)
  append had introduced invalid UTF-8 byte `0x97` at offset 6520 plus mojibake
  (`P0 ??`, `M001 ?`, `→`/`—`). Rewritten UTF-8-safe; `ruff format --check`
  exits 0 again. **Lesson: never use PS 5.1 `Add-Content`/`Set-Content` for
  repo text files; use the UTF-8-safe file tools.**
- 2026-09-27: Added real `__init__.py` files to `src/`, all eight subpackages
  and `workers/` (previously empty dirs → implicit namespace packages with
  `__file__ = None`). mypy now sees 11 source files.
- `pwsh` (PowerShell 7) is not on PATH on this host; the gate must be invoked
  as `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1`.
- 2026-09-27 (M007): This host runs **native PostgreSQL 17 (5432) and 18 (5433)**
  Windows services — never publish the dev container to 5432/5433.
- 2026-09-27 (M007): **Dev DB host port changed 55432 → 65432.** Port 55432
  landed inside a Windows/Hyper-V dynamic exclusion range (55345–55444 per
  `netsh interface ipv4 show excludedportrange protocol=tcp`) and could no
  longer bind. Ranges are dynamic — re-run the netsh check if binding fails
  after a reboot. Updated in `docker-compose.yml`, `.env`, `.env.example`,
  README, and the M003 deviation note in `MILESTONES.md`.
- 2026-09-27 (M007): The opencode host **process** environment carries a stale
  `DATABASE_URL` (port 55432); real env vars override `.env` in
  pydantic-settings, so verification commands must run as
  `$env:DATABASE_URL=$null; <cmd>` until the host process is restarted with
  it unset. Not persisted at User/Machine scope.
- 2026-09-27 (M007): `.env` edit via PS5.1 `Set-Content -Encoding UTF8`
  silently prepended a BOM; stripped via `[System.IO.File]::WriteAllText` with
  `UTF8Encoding($false)`. Reinforces the UTF-8 lesson above — even for
  gitignored local files, prefer the UTF-8-safe file tools.
