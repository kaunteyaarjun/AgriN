# AgriN — Copilot Session Instructions

## Quick Start

**Environment setup:**
```bash
uv sync --extra dev
```

**Quality gate (format → lint → typecheck → tests):**
```bash
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```
(`pwsh` / PowerShell 7 is not on PATH on this host; the gates also run
individually via `uv run ruff|mypy|pytest`.)

**Individual commands:**
- `uv run ruff format .` — format code (mutating)
- `uv run ruff check .` — lint
- `uv run mypy .` — static type-check  
- `uv run pytest` — run all tests
- `uv run pytest -k <test_name>` — run single test by name
- `uv run pytest tests/<file>::<class>::<test>` — run specific test function

## Architecture Overview

AgriN is a modular-monolith FastAPI service + React SPA for digital agriculture intelligence.

**Core vertical (data pipeline → decisions → AI advisory):**
1. **Farm State** (`models/farm_state.py`, `services/farm_state.py`) — aggregates crop, planting date, growth stage, signal cache
2. **External Data Providers** (`services/` + `ai/` modules) — weather, satellite/NDVI, soil ingestion via pluggable provider interface (abstract base + registry pattern)
3. **Analysis Engines** (`services/`) — crop health (rule-based), farm risk (deterministic scoring), crop recommendation
4. **Disease Diagnosis** (`ai/`) — image upload → context-aware assessment blending provider confidence + farm state
5. **Decision Engine** (`services/`) — aggregates health/risk/recommendations
6. **LLM Advisory** (`ai/`) — decision → templated prompt → validated text output
7. **What-if Simulation** (`services/`) — hypothetical re-run of decision pipeline with modified farm state

**Orthogonal concerns:**
- **Auth** (M009–M010): JWT tokens, RBAC roles + permission dependencies
- **Farmer/Farm/Plot domain** (M011–M016): core resource hierarchy with ownership-based authorization (IDOR audit in M017)
- **Database** (`models/`): SQLAlchemy + asyncpg async ORM, Alembic migrations
- **Logging & error handling** (M005): structured via Pydantic settings, not yet implemented
- **Frontend** (M046+): Vite + React + TypeScript + Tailwind; separate repo or monorepo TBD

## Key Conventions

### Package Structure
- `src/core/` — shared utilities, config, constants
- `src/models/` — SQLAlchemy ORM models + migration schemas
- `src/services/` — business logic (farm state, analysis, decision, what-if)
- `src/ingestion/` — external data provider orchestration
- `src/ai/` — AI advisory & disease diagnosis logic (LLM + image processing)
- `src/api/` — FastAPI routers (endpoints by resource + concern)
- `src/admin/` — admin-only endpoints (farmer oversight, review queues)
- `src/interop/` — federation/third-party integration stubs (M060, not yet active)
- `workers/` — async task workers (if background jobs needed later)

### Providers & Registry Pattern
All external providers (weather, satellite, soil, disease, LLM) follow a pluggable interface:
- Abstract base class defines the contract (e.g., `WeatherProvider.fetch()`)
- **Demo provider** included in M0XX (demo data, no external API calls)
- **Live provider** added later (M024, M027, etc.) — swapped in via registry/config without changing caller code
- Provider registration via dependency injection or factory function; select via settings

### Code Organization per Milestone
- Each milestone (M001–M060) is **self-contained** in one or more commits
- `ENGINEERING_STATE.md` tracks current milestone + completion status + known issues
- `MILESTONES.md` defines objectives, acceptance criteria, and failure scenarios upfront
- Migrations are **always named after the milestone** (e.g., `alembic/versions/m004_base_schema.py`)
- New models go in `src/models/`; new endpoints in `src/api/` or `src/admin/`

### Testing
- **Async fixtures:** pytest-asyncio handles `async def test_*()` natively (see `pyproject.toml` `asyncio_mode = "auto"`)
- **Test database:** use in-memory SQLite or Docker Postgres dev instance (per-milestone decision)
- **Smoke test** (`tests/test_smoke.py`) verifies `src/` and `workers/` are importable
- Regression suite consolidated in M057; CI script appended there

### Type Checking
- `mypy` is strict: `check_untyped_defs = true`, `warn_unused_ignores = true`
- All function signatures must have annotations (except test fixtures, `@pytest.fixture` allowed)
- Use `Optional[T]` for nullable fields; never leave a field without an explicit type

### Python & Ruff
- **Python 3.12** pinned in `.python-version` and `pyproject.toml` (`requires-python = ">=3.12,<3.13"`)
- **Ruff line length:** 100 characters (enforced on `src/`, `workers/`, `tests/`)
- **Ruff lint rules:** E (pycodestyle errors), F (Pyflakes), W (pycodestyle warnings), I (isort), B (flake8-bugbear), UP (pyupgrade)
- Ruff format is non-mutating in quality gate; run `uv run ruff format .` to actually format

### Dependencies & Security
- **Runtime:** FastAPI, uvicorn, SQLAlchemy (async), Alembic, asyncpg, Pydantic, passlib[bcrypt], PyJWT
- **Dev:** pytest, pytest-asyncio, httpx, ruff, mypy, bandit, pip-audit
- All versions pinned in `pyproject.toml` (updated per-milestone, not floating)
- Security hardening pass deferred to M055 (rate limits, audit log, security headers, dependency scanning)
- `.env` secrets excluded via `.gitignore`; see `.env.example` for non-secret placeholder keys

### Decision Log
Key architectural decisions (human-confirmed) are logged in `ENGINEERING_STATE.md` under "Checkpoint decisions":
- D1 — Section 3 locked architecture (confirmed 2026-09-26)
- D2 — Dev commands: `uv run ruff|mypy|pytest` + `scripts/check.ps1` (no make/justfile)
- D3 — Password hashing: `passlib[bcrypt]` + pinned `bcrypt==4.0.1` (revisit M055)
- D4 — Authorized system actions: `git init`; Docker Desktop on-demand (M003+)
- D5 — JWT library: **PyJWT** (not python-jose)
- D6 — Python: **3.12** pinned

### Git Workflow
- Commit messages include the milestone ID and objective (e.g., `M001: Set up repository skeleton`)
- Each milestone is one or more commits; rollback strategy defined upfront in milestone spec
- Migrations are committed alongside schema changes; no orphaned migration files

## What's Not Yet Implemented

As of M001 (bootstrap), the following are **future milestones** (not yet implemented):
- Database connectivity & ORM setup (M003)
- Models & migrations (M004+)
- API endpoints (M006+)
- Frontend (M046+)
- Security hardening (M055)
- Deployment (M058)

Refer to `MILESTONES.md` for the full roadmap and interdependencies.

## Useful Links

- **Roadmap:** `MILESTONES.md` — all 60 milestones, status, and specs
- **State tracking:** `ENGINEERING_STATE.md` — current milestone, completed work, known issues, decisions
- **Tests:** `tests/test_smoke.py` — importability checks (more tests added per milestone)
- **Quality gate:** `scripts/check.ps1` — non-mutating format/lint/typecheck/test flow

## Common Tasks

**Start a new milestone:**
1. Update `ENGINEERING_STATE.md`: change `Current milestone` to the new ID and set status to `in-progress`
2. Create or update models/routes/services for the new feature
3. Write tests in `tests/test_<feature>.py`
4. Run `pwsh -File scripts/check.ps1` to verify all checks pass
5. Commit with message `M0XX: <objective>` and a single Co-authored-by trailer
6. Update `MILESTONES.md` and `ENGINEERING_STATE.md`: mark milestone done, set next

**Troubleshoot dependency issues:**
- Clear `.venv` and run `uv sync --extra dev` again
- Check `.python-version` is 3.12
- Verify `pyproject.toml` pinned versions (no floating)

**Run a single test during development:**
```bash
uv run pytest -xvs tests/test_feature.py::test_my_case
```

**Type-check before committing:**
```bash
uv run mypy src/
```
