# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "M004 — Migration tooling & base schema (Alembic init)"
Completed milestones: ["M001", "M002", "M003"]
Current implementation status: "M003 done: async engine/sessionmaker with bounded pool + pool_pre_ping, leak-proof get_db dependency, dev Postgres 16 via docker compose (host port 55432), wait_for_db script, 7 DB tests. No models/migrations yet."
Known bugs: []
Known security issues: []
Known performance issues: []
Known resource/memory issues: []
Technical debt: []
Blocked tasks: []
Next milestone: "M004 — Migration tooling & base schema (Alembic init)"
Last verification: "M003 gate PASSED with live dev DB: ruff format OK, ruff check OK, mypy 18 files OK, pytest 17 passed"
Last test result: "pytest = 17 passed (config 8, db integration 4, db redact 3, smoke 2)"
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
| M003 | `<pending — recorded after commit>` |

## Notes / findings

- 2026-09-27: `MILESTONES.md` repaired. A PowerShell 5.1 `Add-Content` (ANSI)
  append had introduced invalid UTF-8 byte `0x97` at offset 6520 plus mojibake
  (`P0 ??`, `M001 �`, `→`/`—`). Rewritten UTF-8-safe; `ruff format --check`
  exits 0 again. **Lesson: never use PS 5.1 `Add-Content`/`Set-Content` for
  repo text files; use the UTF-8-safe file tools.**
- 2026-09-27: Added real `__init__.py` files to `src/`, all eight subpackages
  and `workers/` (previously empty dirs → implicit namespace packages with
  `__file__ = None`). mypy now sees 11 source files.
- `pwsh` (PowerShell 7) is not on PATH on this host; the gate must be invoked
  as `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1`.
- 2026-09-27: This host runs **native PostgreSQL 17 (5432) and 18 (5433)**
  Windows services. Any dev container published to those ports is shadowed
  (connections hit the native server → wrong password). The AgriN dev DB is
  therefore on host port **55432**. Do not "fix" it back to 5432.
