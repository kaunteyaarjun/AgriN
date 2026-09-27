# AgriN — Milestone Roadmap & Specs

🔒 = **human checkpoint required** before implementing (architecturally
significant — confirm with the human before proceeding, don't just decide
alone). Everything else proceeds autonomously via the Engineering Loop
(Section 4 of the Master Engineering Prompt).

**Status values:** `not-started` → `in-progress` → `done` (committed) /
`failed` (see Failure Protocol).

---

## 1. FULL MILESTONE ROADMAP (M001–M060)

| ID | Milestone | Priority | Depends On | Status |
|---|---|---|---|---|
| **Foundation** | | | | |
| M001 | Repository bootstrap (structure, tooling, pre-commit) | P0 🔒 | — | done |
| M002 | Configuration & secrets management (env-based settings) | P0 | M001 | done |
| M003 | Database connectivity & session lifecycle | P0 | M002 | not-started |
| M004 | Migration tooling & base schema (Alembic init) | P0 | M003 | not-started |
| M005 | Structured logging & error-handling skeleton | P0 | M002 | not-started |
| M006 | FastAPI app skeleton, routers, OpenAPI base | P0 | M002, M005 | not-started |
| M007 | Health/readiness endpoints | P0 | M006 | not-started |
| M008 | User model + password hashing | P0 | M004 | not-started |
| M009 | Auth: login/token issuance (JWT) | P0 | M008, M006 | not-started |
| M010 | RBAC foundation (role enum + permission dependency) | P0 | M009 | not-started |
| **Farmer/Farm/Plot domain** | | | | |
| M011 | Farmer profile model & migration | P0 | M008 | not-started |
| M012 | Farmer CRUD API | P0 | M011, M010 | not-started |
| M013 | Farm model & migration (geo as JSONB) | P0 🔒 | M011 | not-started |
| M014 | Farm CRUD API + ownership authorization | P0 | M013, M010 | not-started |
| M015 | Plot model & migration | P0 | M013 | not-started |
| M016 | Plot CRUD API + ownership authorization | P0 | M015, M010 | not-started |
| M017 | Cross-resource authorization audit (IDOR pass) | P0 | M012, M014, M016 | not-started |
| **Farm Digital Twin** | | | | |
| M018 | Farm State schema (crop, stage, planting date, signal cache) | P0 | M015 | not-started |
| M019 | Farm State service (compute/query) | P0 | M018 | not-started |
| M020 | Farm State API | P0 | M019, M010 | not-started |
| **External providers — interfaces & demo (live = later)** | | | | |
| M021 | Provider interface pattern (abstract base + registry) | P0 🔒 | M002 | not-started |
| M022 | Weather demo provider | P0 | M021 | not-started |
| M023 | Weather ingestion service + storage table | P0 | M022, M019 | not-started |
| M024 | Weather live provider (Open-Meteo) | P1 | M023 | not-started |
| M025 | Satellite/NDVI demo provider | P0 | M021 | not-started |
| M026 | Satellite ingestion service + storage table | P0 | M025, M019 | not-started |
| M027 | Satellite live provider | P1 | M026 | not-started |
| M028 | Soil demo provider | P0 | M021 | not-started |
| M029 | Soil ingestion service + storage table | P0 | M028, M019 | not-started |
| M030 | Soil live provider | P2 | M029 | not-started |
| **Normalization** | | | | |
| M031 | Data normalization layer (units/timeframes → Farm State) | P0 | M023, M026, M029 | not-started |
| **Analysis engines** | | | | |
| M032 | Crop health analysis engine (rule-based) | P0 | M031 | not-started |
| M033 | Farm risk engine (deterministic scoring) | P0 | M031, M032 | not-started |
| M034 | Crop recommendation engine (rule-based) | P0 | M031 | not-started |
| **Disease diagnosis** | | | | |
| M035 | Image upload endpoint (MIME/size/decompression limits) | P0 | M016 | not-started |
| M036 | Disease provider interface + demo provider | P0 | M021, M035 | not-started |
| M037 | Context-aware disease assessment (confidence + farm-state blend) | P0 | M036, M019, M032 | not-started |
| M038 | Disease provider live model integration | P1/P2 | M036 | not-started |
| **Decision engine & AI advisory** | | | | |
| M039 | Structured agricultural decision engine (aggregation) | P0 🔒 | M033, M034, M037 | not-started |
| M040 | LLM provider interface + demo provider (templated) | P0 | M021 | not-started |
| M041 | AI advisory generation service (decision → prompt → validated text) | P0 | M039, M040 | not-started |
| M042 | LLM live provider integration | P0 🔒 | M040 | not-started |
| M043 | Advisory API endpoint | P0 | M041 | not-started |
| **What-if simulation** | | | | |
| M044 | What-if simulation engine (hypothetical re-run of decision pipeline) | P0 | M039 | not-started |
| M045 | What-if simulation API | P0 | M044 | not-started |
| **Frontend** | | | | |
| M046 | Frontend bootstrap (Vite+React+TS+Tailwind, auth flow) | P0 🔒 | M009 | not-started |
| M047 | Farmer dashboard: farm/plot list + farm-state view | P0 | M046, M020 | not-started |
| M048 | Farmer dashboard: health/risk visualization | P0 | M047, M032, M033 | not-started |
| M049 | Farmer dashboard: disease upload + result view | P0 | M047, M037 | not-started |
| M050 | Farmer dashboard: AI advisory display | P0 | M047, M043 | not-started |
| M051 | What-if simulation UI | P1 | M050, M045 | not-started |
| M052 | Admin dashboard: farmer/farm oversight list | P1 | M046, M010 | not-started |
| M053 | Admin dashboard: low-confidence disease review queue | P1 | M052, M037 | not-started |
| **Demo data** | | | | |
| M054 | Deterministic demo data seed script | P0 | M016, M018 | not-started |
| **Hardening passes** | | | | |
| M055 | Security hardening pass (rate limits, audit log, headers, dep scan) | P0 | all API milestones | not-started |
| M056 | Performance & resource review pass | P0 | all service milestones | not-started |
| M057 | Regression suite consolidation + CI script | P0 | all | not-started |
| **Deployment & docs** | | | | |
| M058 | Docker-compose deployment (api+db+web) | P0 🔒 | M057 | not-started |
| M059 | Final documentation pass | P0 | M058 | not-started |
| **Future prep (do not implement beyond the contract)** | | | | |
| M060 | Interop/federation contract stub (schema only, no real sync) | P3 | M059 | not-started |

**Priority legend:** P0 = required for the demo vertical slice · P1 = if time
remains after all P0s are demo-ready · P2/P3 = out of scope for the 3–4 day
build (interface in place, body not implemented).

---

## 2. MILESTONE SPECS

Specs are appended under each milestone's heading as milestones are
elaborated (full Section 5 template for M001–M010 pre-written from the
Master Engineering Prompt; M011+ written just-in-time per Section 8).

<!-- M0XX spec sections are appended here -->

---

### M001 — Repository Bootstrap

**Priority:** P0 🔒 (checkpoint satisfied: Section 3 confirmed as-is on 2026-09-26) **Depends On:** None
**Status:** done

#### Objective
Create the repository skeleton, dependency management, and dev tooling — nothing functional yet.

#### Why This Milestone Exists
Every later milestone needs a place to put code and a way to run lint/format/type-check/test consistently.

#### Files Expected to Be Created
- `pyproject.toml` (pinned dependency list + ruff + mypy + pytest config)
- `.python-version` (pins 3.12, decision D6)
- `.gitignore`, `.env.example`, `README.md` (stub)
- `scripts/check.ps1` (fmt/lint/typecheck/test gate — decision D2 replaces Makefile/justfile)
- `src/` package skeleton: `core/`, `models/`, `services/`, `ingestion/`, `ai/`, `interop/`, `api/`, `admin/`
- `workers/`, `tests/` (+ smoke test so `pytest` exits 0)

#### Files Expected to Be Modified
None beyond the kickoff files.

#### Database Changes
None.

#### API Changes
None.

#### Frontend Changes
None.

#### External Dependencies (pinned, why)
Runtime: `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `alembic`, `asyncpg`, `pydantic-settings`,
`passlib[bcrypt]` + `bcrypt==4.0.1` (decision D3), `PyJWT` (decision D5).
Dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`, `bandit`, `pip-audit`.
Resolved/pinned from PyPI on 2026-09-26 (see pyproject.toml).

#### Implementation Steps
1. Inspect target directory (done: empty, git initialized, uv/Python 3.12 available).
2. `pyproject.toml` with pinned deps, setuptools build (`src*` + `workers*` packages),
   ruff/mypy/pytest config sections.
3. `.python-version` → 3.12.
4. Directory skeleton with `__init__.py` in every package dir.
5. `.env.example` with placeholder non-secret variable names only.
6. README stub (one paragraph; full content in M059).
7. `scripts/check.ps1`: non-mutating gate — `ruff format --check`, `ruff check`, `mypy`, `pytest`.
8. Smoke test (`tests/test_smoke.py`) so `pytest` collects ≥1 test and exits 0.

#### Acceptance Criteria
- [x] `uv sync --extra dev` succeeds from clean.
- [x] `ruff check .` and `mypy .` run without configuration errors.
- [x] `pytest` runs and exits 0.

#### Unit Tests Required
- Smoke: `src` package importable; test collection works.

#### Integration Tests Required
None yet.

#### Security Checks Required
- [x] `.env.example` contains no real secrets.
- [x] `.gitignore` excludes `.env`, `__pycache__`, `.venv`, build artifacts.

#### Performance Checks Required
None yet.

#### Memory/Resource Checks Required
None yet.

#### Failure Scenarios to Handle
Dependency resolution conflicts — versions pinned explicitly rather than floating.

#### Rollback Strategy
Delete the scaffold files; nothing depends on this yet.

#### Verification Commands
```bash
uv sync --extra dev
uv run ruff check .
uv run mypy .
uv run pytest
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5); security/perf/memory sections ticked explicitly.

#### What Must NOT Be Implemented Here
No app code, no DB connection, no models, no endpoints.

#### Notes / deviations (logged, per rule 6)
- Pre-commit role: the `pre-commit` framework is NOT added (not in Section 3 dep list;
  network-dependent git hooks). Gate = `scripts/check.ps1` (decision D2).
- `pytest` "0 tests" acceptance satisfied via an explicit smoke test (exit 0 guaranteed).
- `MILESTONES.md` was repaired after a PowerShell 5.1 `Add-Content` ANSI-encoding
  corruption introduced an invalid UTF-8 byte mid-file; the M001 spec was rewritten
  with a UTF-8-safe writer.
- Real `__init__.py` files were added to `src/` and all subpackages plus `workers/`
  so the editable install resolves concrete packages rather than implicit namespace
  packages (namespace packages reported `__file__ = None`).
- Gate invocation on this host is `powershell -NoProfile -ExecutionPolicy Bypass
  -File scripts/check.ps1` (`pwsh` / PowerShell 7 is not on PATH).

---

### M002 — Configuration & Secrets Management

**Priority:** P0 **Depends On:** M001
**Status:** done

#### Objective
A single typed `Settings` object (Pydantic `BaseSettings`) that loads all configuration
from environment variables, with no hardcoded secrets anywhere.

#### Why This Milestone Exists
Every subsequent milestone (DB, auth, providers) needs configuration. Getting this right
once avoids scattered `os.environ[...]` calls later.

#### Files Expected to Be Created
- `src/core/config.py`
- `tests/core/__init__.py` (test-package marker)
- `tests/core/test_config.py`

#### Files Expected to Be Modified
- `.env.example` (confirm/document variable names)

#### Database Changes
None.

#### API Changes
None.

#### Frontend Changes
None.

#### External Dependencies
`pydantic-settings` (already added in M001). No new dependencies.

#### Implementation Steps
1. Define `Settings(BaseSettings)` with fields: `env` (`dev`/`prod`), `log_level`,
   `database_url`, `jwt_secret`, `jwt_access_ttl_minutes`, `jwt_refresh_ttl_days`,
   `cors_origins`, and provider mode flags (`weather_provider`, `satellite_provider`,
   `soil_provider`, `disease_provider`, `llm_provider` — `demo`/`live`).
2. `get_settings()` cached via `functools.lru_cache` so settings parse once per process.
3. Fail fast and loudly if a required variable is missing in `prod` mode; allow sane
   dev defaults only in `dev` mode.

#### Acceptance Criteria
- [x] App/settings fail with a clear validation error if `jwt_secret` (or
      `database_url`) is missing in prod mode.
- [x] Settings load correctly from a `.env` file in dev mode.
- [x] No fallback secret value that would work in production.

#### Unit Tests Required
- Missing required var in prod mode → clear validation error.
- Valid env → `Settings` populates correctly (incl. dev defaults).
- `get_settings()` returns the same cached instance (parse-once).

#### Integration Tests Required
None.

#### Security Checks Required
- [x] No default/fallback `jwt_secret` that would be usable in prod.
- [x] `jwt_secret` never logged (repr/str of Settings must not expose it).

#### Performance Checks Required
- [x] Settings parsed once (cached), not re-parsed per request.

#### Memory/Resource Checks Required
None significant at this size.

#### Failure Scenarios to Handle
Missing `.env` in dev → fall back to documented dev defaults; in prod → fail fast.

#### Rollback Strategy
Revert `config.py`; nothing else depends on specific field names yet.

#### Verification Commands
```bash
uv run pytest tests/core/test_config.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No DB connection logic, no provider logic — just the settings object.

#### Notes / deviations (logged, per rule 6)
- Provider mode flags are `demo|live` literals validated by Pydantic; provider
  implementations land in later milestones (M022+).
- `cors_origins` uses `pydantic_settings.NoDecode` so a plain comma-separated
  env value is accepted, instead of pydantic-settings' default JSON decoding
  for complex types (which rejected `http://a,http://b`).
