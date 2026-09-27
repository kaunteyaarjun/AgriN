# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "M016 — Plot CRUD API + ownership authorization"
Completed milestones: ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M008", "M009", "M010", "M011", "M012", "M013", "M014", "M015"]
Current implementation status: "M015 done: plots table at Alembic revision 0005 — uuid PK, farm_id FK -> farms(id) ON DELETE CASCADE with btree ix_plots_farm_id, name varchar(120) UNIQUE(farm_id,name), area_hectares numeric(10,2) NULL, geo geometry(Geometry,4326) NULL with GIST idx_plots_geo; Plot model exported (repr hides geo); migration pin moved to 0005. No endpoints (M016), no crop/stage columns (M018)."
Known bugs: []
Known security issues: []
Known performance issues: []
Known resource/memory issues:
  - "Residual (documented, not reproducible locally): asyncio.wait_for cancelling /ready's check mid real-socket cleanup; SQLAlchemy pool handles greenlet cancellation — re-measure in M056. Refused-connection path asserted clean (checkedout()==0)."
Technical debt:
  - "Autogenerate migrations must ALWAYS be hand-reviewed — M008 caught a duplicated same-name CHECK constraint in the generated output."
Blocked tasks: []
Next milestone: "M016 — Plot CRUD API + ownership authorization"
Last verification: "M015 gate PASSED with live dev DB (65432, PostGIS 3.4): ruff format OK, ruff check OK, mypy 55 files OK, pytest 152 passed / 0 skipped (11 new plot); bandit on src/models + 0005 migration = 0 findings. Live: alembic current 0005 (head), downgrade 0004 drops plots only (farms intact), \\d plots = geometry(Geometry,4326) + GIST idx_plots_geo + btree ix_plots_farm_id + unique(farm_id,name) + FK CASCADE."
Last test result: "pytest = 152 passed (plot 11, farms-API 15, farmers-API 15, auth 14, health 9, rbac 11, root 4, config 8, db 4, redact 3, errors 8, logging 4, security 17, user 6, farm-model 11, farmer-model 8, migrations 2, smoke 2)"
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
| D7 | Farm geometry → **PostGIS `geometry(Geometry, 4326)` column** (human-confirmed 2026-09-27; rejected GeoJSON-in-JSONB and plain lat/lng point). DB image becomes `postgis/postgis:16-3.4`, new pinned dep `geoalchemy2`. |

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
| M007 | `0f50ada` |
| M008 | `a7cf3c5` |
| M009 | `1f9996c` |
| M010 | `c477bad` |
| M011 | `ffc6718` |
| M012 | `0060725` |
| M013 | `9e58818` |
| M014 | `0a45a78` |

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
- 2026-09-27 (M009): **Removed stock `fileConfig()` from `alembic/env.py`.**
  Alembic's ini-driven logging config reset the root logger and disabled
  existing `agrin.*` loggers once in-process migrations ran before API tests,
  breaking caplog assertions in `tests/api/test_health.py`. App owns logging
  (`src/core/logging.py`).
- 2026-09-27 (M009): ruff **B008** rejects `Depends(...)` in parameter
  defaults — repo convention is now `Annotated[X, Depends(...)]` (aliases
  `SessionDep`/`CredentialsDep` in `src/api/deps.py`). Use for all future
  FastAPI dependencies/params.
- 2026-09-27 (M009): killing a `uv run uvicorn ...` Start-Process wrapper
  leaves the child python.exe listening on the port — kill by the PID from
  `netstat -ano | Select-String ":8000.*LISTENING"` or the stale server
  serves old code (caused a confusing live 404).
- 2026-09-27 (M010): dev DB `users` table was empty at live verification —
  the container had been recreated between sessions without a named volume
  for that data path. Seeded rows do not survive; re-seed demo users after
  any container recreation (tests unaffected: they seed/clean their own).
- 2026-09-27 (M010): route-handler gates must use the no-default form
  `Annotated[User, Depends(require_role(...))]` — putting `Depends(...)`
  in a parameter *default* trips ruff B008.
- 2026-09-27 (M011): `.gitignore` currently carries an uncommitted local
  edit (`.github` appended, no trailing newline) — not part of M011's
  commit; confirm intent (ignore or track `.github/`) before committing it.
- 2026-09-27 (M012): **Every gate run destroys seeded dev data** —
  `tests/test_migrations.py` round-trip executes `downgrade base` +
  `upgrade head`, reinitializing the whole schema (accounts included).
  Always seed demo users/fixtures **after** the final gate run; a re-gate
  after seeding invalidates the seeds (caused mid-verification 401/405
  confusion). Kept as-is (the round-trip is the point of that test).
- 2026-09-27 (M012): Fixed a second data-wipe source: `test_farmer.py`
  teardowns used unscoped `DELETE FROM users`; now scoped to seeded ids
  (FK cascade cleans their farmer rows). House rule: test cleanup must
  always scope deletes to rows the test created.
