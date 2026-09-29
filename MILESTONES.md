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
| M003 | Database connectivity & session lifecycle | P0 | M002 | done |
| M004 | Migration tooling & base schema (Alembic init) | P0 | M003 | done |
| M005 | Structured logging & error-handling skeleton | P0 | M002 | done |
| M006 | FastAPI app skeleton, routers, OpenAPI base | P0 | M002, M005 | done |
| M007 | Health/readiness endpoints | P0 | M006 | done |
| M008 | User model + password hashing | P0 | M004 | done |
| M009 | Auth: login/token issuance (JWT) | P0 | M008, M006 | done |
| M010 | RBAC foundation (role enum + permission dependency) | P0 | M009 | done |
| **Farmer/Farm/Plot domain** | | | | |
| M011 | Farmer profile model & migration | P0 | M008 | done |
| M012 | Farmer CRUD API | P0 | M011, M010 | done |
| M013 | Farm model & migration (geo as JSONB) | P0 🔒 | M011 | done |
| M014 | Farm CRUD API + ownership authorization | P0 | M013, M010 | done |
| M015 | Plot model & migration | P0 | M013 | done |
| M016 | Plot CRUD API + ownership authorization | P0 | M015, M010 | done |
| M017 | Cross-resource authorization audit (IDOR pass) | P0 | M012, M014, M016 | done |
| **Farm Digital Twin** | | | | |
| M018 | Farm State schema (crop, stage, planting date, signal cache) | P0 | M015 | done |
| M019 | Farm State service (compute/query) | P0 | M018 | done |
| M020 | Farm State API | P0 | M019, M010 | done |
| **External providers — interfaces & demo (live = later)** | | | | |
| M021 | Provider interface pattern (abstract base + registry) | P0 🔒 | M002 | done |
| M022 | Weather demo provider | P0 | M021 | done |
| M023 | Weather ingestion service + storage table | P0 | M022, M019 | done |
| M024 | Weather live provider (Open-Meteo) | P1 | M023 | done |
| M025 | Satellite/NDVI demo provider | P0 | M021 | done |
| M026 | Satellite ingestion service + storage table | P0 | M025, M019 | done |
| M027 | Satellite live provider | P1 | M026 | done |
| M028 | Soil demo provider | P0 | M021 | done |
| M029 | Soil ingestion service + storage table | P0 | M028, M019 | done |
| M030 | Soil live provider | P2 | M029 | not-started |
| **Normalization** | | | | |
| M031 | Data normalization layer (units/timeframes → Farm State) | P0 | M023, M026, M029 | done |
| **Analysis engines** | | | | |
| M032 | Crop health analysis engine (rule-based) | P0 | M031 | done |
| M033 | Farm risk engine (deterministic scoring) | P0 | M031, M032 | done |
| M034 | Crop recommendation engine (rule-based) | P0 | M031, M032 | done |
| **Disease diagnosis** | | | | |
| M035 | Image upload endpoint (MIME/size/decompression limits) | P0 | M016 | done |
| M036 | Disease provider interface + demo provider | P0 | M021, M035 | done |
| M037 | Context-aware disease assessment (confidence + farm-state blend) | P0 | M036, M019, M032 | done |
| M038 | Disease provider live model integration | P1/P2 | M036 | not-started |
| **Decision engine & AI advisory** | | | | |
| M039 | Structured agricultural decision engine (aggregation) | P0 🔒 approved (D9) | M033, M034, M037 | done |
| M040 | LLM provider interface + demo provider (templated) | P0 | M021 | done |
| M041 | AI advisory generation service (decision → prompt → validated text) | P0 | M039, M040 | done |
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

---

### M003 — Database Connectivity & Session Lifecycle

**Priority:** P0 **Depends On:** M002
**Status:** done

#### Objective
An async SQLAlchemy engine + session factory + a FastAPI dependency (`get_db`) that
guarantees sessions are always closed.

#### Why This Milestone Exists
Every model/migration/endpoint milestone from M004 onward needs a working connection
and a leak-proof session lifecycle.

#### Files Expected to Be Created
- `src/core/db.py`
- `docker-compose.yml` (dev `db` service, Postgres 16)
- `scripts/wait_for_db.py`
- `tests/core/test_db.py` (integration; skips if DB unreachable)

#### Files Expected to Be Modified
- `.env.example` (document the dev DB URL used by compose)
- `README.md` (mention `docker compose up -d db`)

#### Database Changes
None yet (no tables) — but the connection is verified against a real Postgres.

#### API Changes
None.

#### Frontend Changes
None.

#### External Dependencies
`asyncpg` + `sqlalchemy[asyncio]` (already added in M001). No new dependencies.

#### Implementation Steps
1. Async engine from `settings.database_url` with sane pool bounds (`pool_size`,
   `max_overflow`, `pool_pre_ping`, `pool_recycle`).
2. Async `sessionmaker` (`async_sessionmaker`, `expire_on_commit=False`).
3. `get_db()` async-generator dependency closing the session in `finally`.
4. Minimal `docker-compose.yml` with a `db` (Postgres 16) service + healthcheck.
5. `scripts/wait_for_db.py` to poll DB readiness before tests/CI race it.

#### Acceptance Criteria
- [ ] App can open and cleanly close a DB session against the compose Postgres.
- [ ] A session is never left open after use, including on an exception.

#### Unit Tests Required
- URL redaction helper (password never visible).

#### Integration Tests Required
- Open a session, run `SELECT 1`, confirm close even if the handler raises.

#### Security Checks Required
- [ ] `database_url` never logged with the password visible.

#### Performance Checks Required
- [ ] Connection pooling configured with sane bounds (not unlimited, not 1).

#### Memory/Resource Checks Required
- [ ] Repeated `get_db` iteration (100x) does not leak connections — check
      `pg_stat_activity` / pool checked-out count before and after.

#### Failure Scenarios to Handle
DB unreachable at startup → clear error, not a silent hang.

#### Rollback Strategy
Revert `db.py`; nothing depends on schema yet.

#### Verification Commands
```bash
docker compose up -d db
uv run python -m scripts.wait_for_db
uv run pytest tests/core/test_db.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No models, no migrations yet — just the connection/session plumbing.

#### Notes / deviations (logged, per rule 6)
- `get_db` is defined with a lazy engine/sessionmaker accessor so importing
  `src.core.db` does not require a reachable DB at import time.
- Integration tests skip (not fail) when the dev DB is unreachable, so the
  non-DB quality gate stays green on hosts without Docker running.
- **Deviation:** compose maps Postgres to host port `65432`, not `5432`.
  This host already runs native PostgreSQL 17 (port 5432) and 18 (port 5433)
  Windows services, which shadowed the container's published port and caused
  `password authentication failed`. Remapping avoids stopping the user's
  existing services. The dev URL also uses `ssl=disable` (the local container
  has no TLS; asyncpg otherwise attempts an SSL upgrade and errors).
- `pip install` of Docker image `postgres:16` initially failed with a
  transient Docker Hub TLS handshake error; a retry succeeded.
- Finding (worth remembering): native Postgres services on 5432/5433 will
  shadow any dev container published to those ports — keep dev DB off 5432/5433.
- Port history: the dev port was originally `55432`; during M007 verification
  (2026-09-27) `docker compose up -d db` failed with `bind: ...forbidden by
  its access permissions` because Windows/Hyper-V had dynamically excluded
  range 55345–55444 (which covers 55432). Moved to `65432` — outside all
  ranges from `netsh interface ipv4 show excludedportrange protocol=tcp`.
  **Re-check the exclusion list if binding ever fails again after a reboot
  (these ranges are dynamic).**

---

### M004 — Migration Tooling & Base Schema

**Priority:** P0 **Depends On:** M003
**Status:** done

#### Objective
Alembic wired up and producing a real, empty-but-working migration chain against the
configured database, with a shared `Base.metadata` for future autogeneration.

#### Why This Milestone Exists
Every model milestone from M008 onward creates tables via migrations; the chain must
be proven to upgrade *and* downgrade cleanly before real schema exists.

#### Files Expected to Be Created
- `alembic.ini`
- `alembic/env.py`, `alembic/script.py.mako`
- `alembic/versions/0001_init.py` (empty baseline revision)
- `src/models/base.py` (`Base` declarative class + shared `metadata`)
- `tests/test_migrations.py` (skips if DB unreachable; upgrade→downgrade→upgrade)

#### Files Expected to Be Modified
- `pyproject.toml` (ruff/mypy exclude `alembic/versions` if generated code trips them)

#### Database Changes
Creates Alembic's own `alembic_version` bookkeeping table only.

#### API Changes
None.

#### Frontend Changes
None.

#### External Dependencies
`alembic` (already added in M001). No new dependencies.

#### Implementation Steps
1. `alembic init` (async-aware) to scaffold `alembic/`.
2. Point the URL at `settings.database_url` via `env.py` (never hardcoded in
   `alembic.ini`); wire `target_metadata = Base.metadata`.
3. Generate and apply the empty baseline revision (`0001_init`).
4. Round-trip test: `upgrade head` → `downgrade base` → `upgrade head`.

#### Acceptance Criteria
- [x] `alembic upgrade head` succeeds against the dev DB from a clean state.
- [x] `alembic downgrade base` cleanly removes everything it created.
- [x] Applying twice is idempotent (Alembic native — verified).

#### Unit Tests Required
- None (inherently integration).

#### Integration Tests Required
- Upgrade → downgrade → upgrade round-trip against the dev DB (skip if unreachable).

#### Security Checks Required
- [ ] DB URL for migrations comes from settings/env, never hardcoded.

#### Performance Checks Required
None at this size.

#### Memory/Resource Checks Required
None at this size.

#### Failure Scenarios to Handle
Migration applied twice — must be idempotent (verify).

#### Rollback Strategy
`alembic downgrade base`.

#### Verification Commands
```bash
docker compose up -d db
uv run alembic upgrade head
uv run alembic downgrade base
uv run alembic upgrade head
uv run pytest tests/test_migrations.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No real domain tables yet — this is plumbing only.

#### Notes / deviations (logged, per rule 6)
- `alembic/env.py` loads the async URL from `Settings` at runtime; `alembic.ini`
  retains no real URL (safe to commit).
- Generated Alembic scaffolding is kept in the quality gate (formatted/linted);
  `alembic/versions/*.py` gets a `F401` per-file ignore because the template
  imports `op`/`sa` for future revisions.

---

### M005 — Structured Logging & Error-Handling Skeleton

**Priority:** P0 **Depends On:** M002
**Status:** done

#### Objective
JSON-structured logging and a global exception handler that never leaks stack traces
or secrets to API clients.

#### Why This Milestone Exists
Every endpoint and service from M006 onward needs consistent, safe logging and error
responses; establishing the primitives now avoids ad-hoc `print`/`except` scattered
later.

#### Files Expected to Be Created
- `src/core/logging.py` (JSON formatter + `configure_logging()`)
- `src/core/errors.py` (`AppError` hierarchy + FastAPI handler registration)
- `tests/core/test_errors.py`
- `tests/core/test_logging.py`

#### Files Expected to Be Modified
None.

#### Database Changes
None.

#### API Changes
None yet (M006 registers the handlers with the app).

#### Frontend Changes
None.

#### External Dependencies
None new.

#### Implementation Steps
1. JSON log formatter emitting `timestamp`, `level`, `logger`, `message`, and
   structured `extra` fields; safe fallback for non-serializable objects.
2. `configure_logging(level)` keyed by `settings.log_level`, idempotent.
3. `AppError` base exception with stable `error_code`, human-safe `message`, and
   HTTP `status_code`; a few standard subclasses.
4. `register_exception_handlers(app)`:
   - `AppError` → its status + sanitized `{error_code, message}`.
   - unhandled `Exception` → generic 500 body, full traceback only to the server log.

#### Acceptance Criteria
- [x] An unhandled exception returns a generic 500 JSON body to the client and a
      full traceback in the server log.
- [x] A raised `AppError` returns its mapped status code and safe message.
- [x] Log output is valid JSON.

#### Unit Tests Required
- `AppError` → correct status/body.
- Unhandled exception → generic body, no stack trace/exception text in response.
- JSON formatter handles non-serializable objects without raising.

#### Integration Tests Required
- Minimal FastAPI app exercising both handlers via `httpx.ASGITransport`.

#### Security Checks Required
- [x] No stack traces, SQL, or file paths in client-facing error responses.
- [x] No secrets in logs.

#### Performance Checks Required
None at this size.

#### Memory/Resource Checks Required
None at this size.

#### Failure Scenarios to Handle
Logging itself throwing (non-serializable object) must not crash the request —
fall back to a safe repr.

#### Rollback Strategy
Revert the two files; nothing depends on error shapes yet.

#### Verification Commands
```bash
uv run pytest tests/core/test_errors.py tests/core/test_logging.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No endpoints yet — this is pure infrastructure.

#### Notes / deviations (logged, per rule 6)
- Handlers are exposed via `register_exception_handlers(app)` for M006 to call;
  tests build a throwaway app so M005 stays app-free.

---

### M006 — FastAPI App Skeleton, Routers, OpenAPI Base

**Priority:** P0 **Depends On:** M002, M005
**Status:** done

#### Objective
A running FastAPI app with the router/versioning pattern established (`/api/v1/...`),
wired to config, logging, and error handling.

#### Why This Milestone Exists
Every endpoint milestone (M007, M009, M012, ...) mounts onto this app; the versioning
and middleware conventions must be set once, correctly.

#### Files Expected to Be Created
- `src/main.py` (app factory + `app` instance)
- `src/api/__init__.py` unchanged; `src/api/v1/__init__.py` (v1 router aggregator)
- `tests/api/__init__.py`, `tests/api/test_root.py`

#### Files Expected to Be Modified
- `.env.example` (document `CORS_ORIGINS` already present; no new vars)

#### Database Changes
None.

#### API Changes
`GET /` → app metadata `{name, version, environment}`.

#### Frontend Changes
None.

#### External Dependencies
None new (`fastapi`, `uvicorn` already present).

#### Implementation Steps
1. `create_app()` factory: configures logging, registers exception handlers (M005),
   mounts the `/api/v1` aggregator (empty), sets OpenAPI title/version/description.
2. Explicit CORS allow-list from `settings.cors_origins` (never `*`).
3. Fail fast at startup if settings are invalid (prod secret check already in M002).
4. `GET /` returns name/version/environment; test via `httpx.ASGITransport`.

#### Acceptance Criteria
- [x] `uvicorn src.main:app` starts cleanly.
- [x] `GET /docs` loads.
- [x] `GET /` returns app name/version JSON.

#### Unit Tests Required
- None beyond the API test.

#### Integration Tests Required
- `GET /` → 200 with expected shape; `GET /openapi.json` → 200.

#### Security Checks Required
- [x] CORS is explicit, not wildcard.
- [x] `/docs` exposure is a deliberate decision, noted in the milestone log.

#### Performance Checks Required
- [ ] App startup does not block on slow external calls.

#### Memory/Resource Checks Required
None at this size.

#### Failure Scenarios to Handle
Invalid settings at startup → fail fast with a clear log line.

#### Rollback Strategy
Revert `main.py`; nothing depends on it yet beyond imports.

#### Verification Commands
```bash
uv run pytest tests/api/test_root.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No auth, no domain endpoints yet.

#### Notes / deviations (logged, per rule 6)
- `/docs` stays enabled (open API docs are wanted for the hackathon demo);
  noted here as a deliberate choice, revisited at M055.
- The lifespan handler configures logging; DB connectivity is exercised by
  `/ready` in M007, so startup does not hard-fail when the DB is briefly down.

---

### M007 — Health/Readiness Endpoints

**Priority:** P0 **Depends On:** M006
**Status:** done

#### Objective
`/health` (liveness — process is up) and `/ready` (readiness — DB reachable)
so the docker-compose stack and any future orchestration can check status.

#### Why This Milestone Exists
Operators (and later M058's compose stack) need a way to distinguish "process
alive" from "actually able to serve" without reading logs.

#### Files Expected to Be Created
- `src/api/health.py` (router with the two probes)
- `tests/api/test_health.py`

#### Files Expected to Be Modified
- `src/main.py` (mount the health router at app root, not under `/api/v1`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None.

#### API Changes
- `GET /health` → 200 `{"status": "ok"}` always (no dependencies, no auth).
- `GET /ready` → 200 `{"status": "ready"}` if DB answers `SELECT 1` within a
  2s timeout; 503 `{"status": "unavailable"}` otherwise. Public, no auth,
  no internal detail in the body.

#### Frontend Changes
None.

#### External Dependencies
None new (`asyncio.wait_for` from stdlib).

#### Implementation Steps
1. Router in `src/api/health.py`: `/health` returns immediately; `/ready`
   opens a raw connection from the shared engine (`engine.connect()` +
   `SELECT 1`) wrapped in `asyncio.wait_for(..., timeout=READY_TIMEOUT_S=2.0)
   so a DB *hang* becomes a fast 503. Catches `Exception` broadly but only
   returns `{"status": "unavailable"}` — detail goes to the server log.
2. Mount router in `create_app()` at root (probes stay outside `/api/v1`
   so infra tooling needs no version knowledge).
3. Tests: health-always-200, ready-200-skip-if-no-db, ready-503-on-error,
   ready-503-on-hang (fast, measured < timeout+ε), no-detail-leak,
   no-connection-leak on the failure path.
4. Manual live verification: DB up → 200; `docker compose stop db` → 503;
   restart DB.

#### Acceptance Criteria
- [x] `/health` returns 200 even if the DB is down. (verified live: DB
      stopped → `/health` still 200)
- [x] `/ready` returns 503 if the DB is down, 200 if up. (verified live
      across stop/start of the compose db container)
- [x] `/ready` converts a DB *hang* into a fast 503 (explicit timeout;
      hang test measures elapsed within [2.0s, 4.5s)).
- [x] Neither endpoint leaks internal detail (no stack traces, SQL, paths) —
      tests assert exact response bodies.

#### Unit Tests Required
- [x] Mocked DB failure → `/ready` returns 503 with generic body.
- [x] Mocked DB hang → `/ready` returns 503 promptly (elapsed < ~4.5s).

#### Integration Tests Required
- [x] Real DB up → `/ready` returns 200 (ran with dev Postgres, 0 skips).
- [x] `/health` returns 200 with no DB involvement (fails if engine touched).

#### Security Checks Required
- [x] These endpoints leak no internal detail beyond up/down status.
- [x] No auth on these endpoints (infra probes: public but non-revealing;
      logged for the M010 public allow-list).

#### Performance Checks Required
- [x] `/ready`'s DB check has an explicit timeout (doesn't hang the endpoint
      — measured, hang test bounds elapsed time).

#### Memory/Resource Checks Required
- [x] Failure paths leave no checked-out pool connections (real-engine
      refused-connection test asserts `pool.checkedout() == 0`).

#### Failure Scenarios to Handle
- DB unreachable → 503, not 500.
- DB hangs (not just errors) → timeout converts hang into fast 503.
- Engine not yet configured (no `DATABASE_URL`) → 503, not unhandled exception.

#### Rollback Strategy
Revert `src/api/health.py` and the mount line in `main.py`; nothing depends
on these routes.

#### Verification Commands
```bash
uv run pytest tests/api/test_health.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: uvicorn src.main:app → curl /health, /ready; compose stop db → 503
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No auth on these endpoints; no DB schema changes; no `/api/v1` prefix; no
orchestration/deployment config (that's M058).

#### Notes / deviations (logged, per rule 6)
- **Environment finding:** during live verification `docker compose up -d db`
  failed with `bind: ...forbidden by its access permissions` — host port
  55432 had fallen inside a Windows/Hyper-V dynamic exclusion range
  (55345–55444 from `netsh ... excludedportrange`). Dev DB host port moved
  `55432 → 65432` (verified outside all listed ranges); `docker-compose.yml`,
  `.env`, `.env.example`, README and the M003 deviation note updated.
- **Environment finding:** this opencode host process carries a stale
  `DATABASE_URL` env var (port 55432) in its process environment; real env
  vars override `.env` in pydantic-settings. Verification commands must be
  run as `$env:DATABASE_URL=$null; <cmd>` or they hit the wrong port. Not
  set at User/Machine scope, so it dies with the host process.
- Residual (documented, not fixed): if `asyncio.wait_for` cancels the check
  exactly while a real connection is mid-cleanup, SQLAlchemy's pool handles
  the greenlet cancellation; the refused-connection test covers the common
  error path (`checkedout()==0`). A true mid-socket hang during cancellation
  is not reproducible locally — noted for the M056 resource pass.

---

### M008 — User Model + Password Hashing

**Priority:** P0 **Depends On:** M004
**Status:** done

#### Objective
A `users` table (email, hashed password, role, timestamps) and a hashing
utility — no endpoints yet.

#### Why This Milestone Exists
Auth (M009) and RBAC (M010) need somewhere to store users and a correct,
salted password hash; getting the schema + hashing right here keeps M009
purely about token issuance.

#### Files Expected to Be Created
- `src/models/user.py` (`User` model + `UserRole` enum)
- `src/core/security.py` (`hash_password`/`verify_password` + async wrappers)
- `alembic/versions/0002_users.py` (hand-reviewed migration)
- `tests/models/__init__.py`, `tests/models/test_user.py`
- `tests/core/test_security.py`

#### Files Expected to Be Modified
- `src/models/__init__.py` (export `Base`/`User` so the package registers tables)
- `alembic/env.py` (import `src.models` so `--autogenerate` sees all tables)
- `tests/test_migrations.py` (head revision `0001` → `0002`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
New `users` table (Alembic revision `0002`, down_revision `0001`):
`id uuid pk`, `email varchar(320) unique`, `password_hash varchar(128)`,
`role varchar(32) + CHECK (farmer|extension_officer|admin)`,
`is_active boolean not null default true`, `created_at timestamptz
server_default now()`, `updated_at timestamptz server_default now()`.
Role is modeled with `sa.Enum(native_enum=False, create_constraint=True)` —
a DB-level CHECK constraint, deliberately **not** a native PG enum type
(native types don't get dropped by `drop_table`, which breaks the
upgrade→downgrade→upgrade round-trip test; documented deviation, still
enforced at the DB level, not just in app code).

#### API Changes
None.

#### Frontend Changes
None.

#### External Dependencies
None new — `passlib[bcrypt]==1.7.4` + `bcrypt==4.0.1` already pinned (D3).

#### Implementation Steps
1. `UserRole` (str Enum) + `User(Base)` model per the schema above;
   `email` unique=True (PG unique constraint ⇒ implicit index; no separate
   redundant non-unique index).
2. `src/core/security.py`: sync `hash_password`/`verify_password`
   (bcrypt, explicit `rounds=12`; malformed hash → `verify` returns False,
   never raises) + async wrappers `hash_password_async`/`verify_password_async`
   that run the sync core via `asyncio.to_thread` so request handlers never
   block the event loop (M009 must use the async forms).
3. `src/models/__init__.py` exports; `alembic/env.py` imports the package so
   autogenerate sees `users`.
4. Generate migration with `alembic revision --autogenerate`, then
   **hand-review the diff** (unique constraint + CHECK must both be present).
5. Update `tests/test_migrations.py` head-revision assertions (`0002`).
6. Tests: unit (round-trip, salted, wrong password, malformed hash, bcrypt
   work factor, plaintext never stored, async wrappers run off-loop) +
   DB integration (duplicate email → IntegrityError, skip if no DB).

#### Acceptance Criteria
- [x] Migration applies and rolls back cleanly (`upgrade head` →
      `downgrade -1` → `upgrade head` — verified manually and by the
      test_migrations round-trip at revision 0002).
- [x] `email` has a unique constraint enforced at the DB level (duplicate
      insert raises IntegrityError — integration test on real Postgres).
- [x] Passwords are never stored in plaintext, anywhere, including logs
      (hash-prefix/plaintext tests; `security.py` does no logging; bandit 0).

#### Unit Tests Required
- [x] Hash/verify round-trip works; wrong password fails verification.
- [x] Same password hashed twice produces different hashes (salted).
- [x] Malformed/garbage stored hash → verify returns False (no exception).
- [x] Parsed bcrypt rounds == 12 (explicit work factor).
- [x] Hashed output contains no plaintext password; starts with `$2b$`.
- [x] Async wrappers execute the hashing in a worker thread, not the event
      loop (thread-identity captured inside a monkeypatched core).

#### Integration Tests Required
- [x] Inserting a duplicate email raises `IntegrityError` (real dev Postgres).
- [x] Migration round-trip with `users` at head (test_migrations at 0002).

#### Security Checks Required
- [x] Bcrypt work factor reasonable and explicit (12; revisit in M055 per D3).
- [x] No password ever appears in a log line, error message, or exception —
      `src.core.security` does no logging; `User.__repr__` omits the hash
      (asserted by test).

#### Performance Checks Required
- [x] Hashing runs off the event loop — verified by thread-identity tests
      for both async wrappers.

#### Memory/Resource Checks Required
- [x] Sessions closed in `finally`, engine disposed in fixture teardown;
      suite runs repeatedly with no pool exhaustion (59/59 green, 0 skips).

#### Failure Scenarios to Handle
- Autogenerate misses the unique constraint or CHECK — inspect and hand-fix
  the migration file, don't trust it blindly.
- Stored hash corrupted/truncated → verification returns False, no crash.
- Migration applied twice → idempotent (Alembic native; round-trip test).

#### Rollback Strategy
`alembic downgrade -1` removes `users`; revert the source files (nothing
depends on them until M009).

#### Verification Commands
```bash
uv run alembic upgrade head
uv run alembic downgrade -1 && uv run alembic upgrade head
uv run pytest tests/core/test_security.py tests/models/test_user.py tests/test_migrations.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No login endpoint, no JWT issuance (M009), no `require_role` (M010), no
email normalization/case-folding policy (deferred until registration
endpoints exist — noted so M009/M012 handle lookup consistently), no
password-reset flows.

#### Notes / deviations (logged, per rule 6)
- Role column uses VARCHAR+CHECK instead of a native PG enum (rationale in
  Database Changes) — semantically still a DB-enforced enum.
- Async wrappers added beyond Section 7's sync-only wording to satisfy this
  milestone's own performance check (hashing must not block the loop).
- **Autogenerate bug (caught by hand-review):** the generated migration
  emitted the role CHECK constraint **twice with the same name**
  (once via `sa.Enum(create_constraint=True)` on the column, once as an
  explicit table constraint) — PostgreSQL rejects that. Migration rewritten
  by hand keeping only the column-owned CHECK. Confirms the standing rule:
  **never trust autogenerate blindly.**
- **Test bug found & fixed:** both DB tests initially failed to *request* the
  `_db` fixture, so its `dispose_engine()` teardown never ran; test A's pooled
  connections (bound to A's closed event loop) poisoned test B deterministically
  (`Event loop is closed`), and the leaked engine cache even caused a
  misleading SKIP in `test_migrations`. Lesson: an async DB test must request
  the fixture that owns engine disposal — asserted by the 59/59 green suite.
- `mypy` types `User.__table__` as `FromClause` (no `.name`/`.constraints`) —
  tests `cast(Table, ...)` explicitly.

---

### M009 — Auth: Login/Token Issuance (JWT)

**Priority:** P0 **Depends On:** M008, M006
**Status:** done

#### Objective
`POST /api/v1/auth/login` issuing a short-lived JWT access token + a refresh
token; `POST /api/v1/auth/refresh` to rotate the access token; plus the
`get_current_user` dependency every protected route will use.

#### Why This Milestone Exists
Nothing downstream (RBAC, farmer/farm CRUD, everything behind auth) works
without a correct, non-enumerating login flow and a trustworthy way to
resolve a bearer token to a `User`.

#### Files Expected to Be Created
- `src/api/v1/auth.py` (login + refresh router)
- `src/api/deps.py` (`get_current_user` FastAPI dependency)
- `tests/api/test_auth.py`

#### Files Expected to Be Modified
- `src/core/security.py` (JWT encode/decode helpers, PyJWT/HS256)
- `src/core/errors.py` (`InvalidCredentials`, `InvalidToken` AppError subclasses)
- `src/api/v1/__init__.py` (mount auth router)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None (reads `users` from M008).

#### API Changes
- `POST /api/v1/auth/login` — body `{email, password}` → 200
  `{access_token, refresh_token, token_type: "bearer"}`; 401
  `{error_code: "invalid_credentials", message: "Invalid email or password."}`
  for unknown email, wrong password (identical body — no enumeration);
  403 `account disabled` only *after* password verification.
- `POST /api/v1/auth/refresh` — body `{refresh_token}` → 200 with a new
  access token (same shape); 401 `invalid_token` for expired/tampered/
  wrong-type tokens or missing/disabled user.
- Protected-route contract (used from M010 on):
  `Authorization: Bearer <access>` → `get_current_user` → `User`;
  missing/malformed/expired/tampered/wrong-type header → 401, never 500.

#### Frontend Changes
None.

#### External Dependencies
None new — `PyJWT==2.15.0` already pinned (D5).

#### Implementation Steps
1. `src/core/security.py`: `create_access_token(user_id)` /
   `create_refresh_token(user_id)` (claims: `sub` str, `type`, `iat`, `exp`
   from settings TTLs; **HS256**, secret from `settings.jwt_secret`, clear
   `RuntimeError` if unset — no insecure fallback) and `decode_token(token,
   expected_type)` raising `InvalidToken` (401) on expiry/tamper/type-mismatch
   (5s clock leeway; `require` exp+sub).
2. `src/core/errors.py`: add `InvalidCredentials` (401) and `InvalidToken`
   (401) with stable error codes.
3. `src/api/v1/auth.py`: login (constant-time-ish: always run a bcrypt
   verify — dummy-hash path when the email is unknown — so "no such user"
   and "wrong password" cost the same and return identical bodies; use the
   **async** hashing wrappers so the loop never blocks); refresh (decode as
   type `refresh`, load user, must exist + be active, issue new access token).
4. `src/api/deps.py`: `get_current_user` via `HTTPBearer(auto_error=False)`
   (missing header → our own 401, not FastAPI's 403 quirk) → decode as type
   `access` → load user by `sub` (one PK SELECT — the only DB hit) →
   401 if missing or `is_active=False`.
5. Mount `auth_router` in `/api/v1`.
6. Tests (skip-if-unreachable `_db` fixture pattern from M008, fixture
   actually requested by every DB test):
   - unit: token round-trip claims, type mismatch, tampered signature,
     expired token raises.
   - API: login success (seeded user) → decodeable tokens; wrong password vs
     unknown email → identical 401 bodies; inactive + correct password → 403;
     refresh happy path; access-into-refresh → 401; protected test route with
     valid/expired/tampered/missing/malformed credentials; disabled user's
     valid token → 401; deleted user's refresh → 401.

#### Acceptance Criteria
- [x] Valid credentials → valid access+refresh tokens (decodable, correct
      claims/TTLs).
- [x] Invalid credentials → 401 with identical body for "no such user" and
      "wrong password" (no user-enumeration leak).
- [x] Expired/tampered access token → 401 on any protected route.
- [x] Refresh token cannot be used as an access token and vice versa.
- [x] Missing/malformed Authorization header → clean 401, not 500/403.

#### Unit Tests Required
- Token encode/decode round-trip; tampered token rejected; expired token
  rejected; wrong `type` rejected.

#### Integration Tests Required
- Full login → access protected route → refresh → access again, end to end
  (real dev Postgres).

#### Security Checks Required
- [x] Timing-safe password comparison (passlib verify — used correctly on
      both user-found and user-missing paths).
- [x] No user-enumeration via error bodies (identical JSON asserted) —
      equalized work via dummy-hash verify (bcrypt timing not precisely
      measured; structural equality of work verified by code path + tests).
- [x] JWT secret only from settings/env, never logged; fail-fast if unset.
- [x] Access TTL 15 min default; refresh TTL 7 days default (both from
      settings, asserted from claims).
- [x] Login rate limiting **flagged for M055** (not implemented here).

#### Performance Checks Required
- [x] Token decode does one PK SELECT per request (load current user) and
      no unnecessary DB hits; hashing runs off the event loop (M008 wrappers).

#### Memory/Resource Checks Required
None significant (stateless tokens; sessions per-request via `get_db`).

#### Failure Scenarios to Handle
- `jwt_secret` unset → clear 500-class failure with log line, no silent
  fallback secret.
- Clock skew → 5s leeway on exp/iat.
- Malformed Authorization header → 401, not an unhandled exception.
- User deleted/disabled between token issue and use → 401/403 handled at
  the dependency/route, not a crash.

#### Rollback Strategy
Remove `src/api/v1/auth.py` + `src/api/deps.py` and the router mount;
`users` table (M008) unaffected.

#### Verification Commands
```bash
uv run pytest tests/core/test_security.py tests/api/test_auth.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: curl -X POST /api/v1/auth/login with seeded credentials
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No RBAC enforcement (`require_role` is M010), no registration endpoint,
no token revocation/logout (refresh tokens are stateless — noted as a
production hardening item for SECURITY.md/M055), no rate limiting (M055).

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 41 files OK,
  pytest **81 passed / 0 skipped** (22 new: 8 JWT unit + 14 auth API);
  bandit on `src/api` + `security.py` + `errors.py` = 0 findings.
- Live (uvicorn + dev DB): login → 200 `bearer` tokens (209/211 chars);
  wrong password and unknown email both → 401 `invalid_credentials`
  with identical body; refresh → 200 new access token; access token at
  `/refresh` → 401 `invalid_token`; routes visible in `/openapi.json`.
- **Finding:** stock alembic `env.py` calls `logging.config.fileConfig()` —
  once in-process migrations ran *before* API tests (test_auth seeds the
  DB), alembic.ini's `fileConfig` reset the root logger and disabled
  `agrin.*` loggers, breaking M007's caplog assertion. Removed the call
  from `alembic/env.py` (app configures its own logging); test_health
  green again when run after test_auth.
- **Finding:** ruff B008 rejects `Depends(...)` in parameter defaults —
  adopted `Annotated[X, Depends(...)]` style (`SessionDep`,
  `CredentialsDep` aliases in `src/api/deps.py`); use this style for all
  future dependencies.
- Deferred to M055 (flagged here): login rate limiting, refresh-token
  revocation/logout.

---

### M010 — RBAC Foundation (role enum + permission dependency)

**Priority:** P0 **Depends On:** M009
**Status:** done

#### Objective
Turn M009's authentication into authorization with one reusable dependency
factory: `require_role(*roles)` — unauthenticated → 401, authenticated but
wrong role → 403 `permission_denied`, allowed role → the `User`. Plus the
`CurrentUserDep` alias for plain "any signed-in user" routes. The role enum
itself (`UserRole`: farmer / extension_officer / admin) already exists from
M008.

#### Why This Milestone Exists
Every privileged route downstream (farm/plot ownership in M014/M016,
extension-officer workflows, admin oversight in M052) needs default-deny
access control. Building it once here means later milestones just annotate
their routes instead of reinventing checks.

#### Files Expected to Be Created
- `tests/api/test_rbac.py`

#### Files Expected to Be Modified
- `src/api/deps.py` (`require_role`, `CurrentUserDep`, `AdminUserDep`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None (role column + VARCHAR/CHECK constraint from M008).

#### API Changes
No new endpoints. Route-level contract from M010 on:
- `user: Annotated[User, Depends(require_role(UserRole.admin))]` —
  401 `not_authenticated`/`invalid_token` before any role logic;
  403 `{error_code: "permission_denied", message: "You do not have
  permission to perform this action."}` (static body, no role details) for
  a signed-in user whose role is not among the declared ones; 200 otherwise.
- **Role source is the DB column, read inside the existing single PK
  SELECT** — no role claim in the JWT, so a role change takes effect on the
  very next request without re-issuing tokens.

#### Frontend Changes
None.

#### External Dependencies
None.

#### Implementation Steps
1. `src/api/deps.py`: add `CurrentUserDep = Annotated[User,
   Depends(get_current_user)]`.
2. Add `require_role(*roles: UserRole)` factory: **fail fast** with
   `ValueError` if called with zero roles (definition time, not request
   time); inner async dependency takes `CurrentUserDep`, raises
   `PermissionDenied` (already exists, 403, M005) unless
   `user.role in frozenset(roles)` (StrEnum makes `"admin"`-style strings
   compare equal too), returns the `User`.
3. Add `AdminUserDep` alias for `require_role(UserRole.admin)` (first real
   consumer: M052).
4. Tests in `tests/api/test_rbac.py` (own `_db` skip-if-unreachable fixture
   + `_app` with gated test routes, seeded farmer/extension_officer/admin):
   see test lists below.

#### Acceptance Criteria
- [x] Gated route + no/malformed/expired/wrong-scheme token → 401, never
      403 or 500 (401 strictly precedes role logic).
- [x] Signed-in user with a non-allowed role → 403 `permission_denied` with
      static body (no role/permission disclosure).
- [x] User with any of the declared roles → 200; multi-role gates work.
- [x] `require_role()` with zero roles raises `ValueError` at definition.
- [x] Changing a user's role in the DB flips access for the *same* token
      (role read from DB, not token).
- [x] Inactive user's otherwise-valid token → 401 (M009 behavior intact).

#### Unit Tests Required
- `require_role()` empty-args → `ValueError`; role membership accepts both
  `UserRole` members and plain strings (StrEnum equality).

#### Integration Tests Required
- Route × role matrix against real dev Postgres: farmer/extension_officer/
  admin × `/any`-style (`CurrentUserDep`), single-role and multi-role
  (`require_role`) routes, plus the role-change re-evaluation case.

#### Security Checks Required
- [x] Default-deny: access requires explicitly declared roles; no implicit
      hierarchy — **admin does not silently pass other gates** (routes name
      `UserRole.admin` explicitly).
- [x] 401 before 403: unauthenticated callers learn nothing about which
      roles exist (403 body is the generic static message).
- [x] Role comes from the DB row (fresh), never from token claims
      (prevents stale-privilege via long-lived refresh tokens).

#### Performance Checks Required
- [x] Gated request still performs exactly one PK SELECT (role rides along
      on the user already loaded by `get_current_user`).

#### Memory/Resource Checks Required
None significant (stateless dependency; per-request session unchanged).

#### Failure Scenarios to Handle
- `require_role()` misused with no roles → `ValueError` at import/definition.
- Deleted/disabled user → 401 via `get_current_user` (unchanged).
- Corrupt/unknown role string in DB → not in the allowed set → denied
  (safe default); the M008 CHECK constraint prevents it from occurring.

#### Rollback Strategy
Remove the M010 additions from `src/api/deps.py`; no DB or endpoint
surface to unwind.

#### Verification Commands
```bash
uv run pytest tests/api/test_rbac.py tests/api/test_auth.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No object-level/ownership checks (M014/M016 authorize per-resource), no
role hierarchy or auto-elevation, no JWT role claim, no role-management
endpoint (user administration later), no middleware-based authorization
(dependency-based only).

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 42 files OK,
  pytest **92 passed / 0 skipped** (11 new RBAC: fail-fast ValueError,
  StrEnum string membership, auth-required, farmer/officer/admin ×
  any/single/multi-role route matrix, wrong-scheme 401, DB role-change
  re-evaluation with the same token, deactivated-user 401);
  bandit on `src/api` = 0 findings.
- Live (uvicorn + dev DB): `/health` 200, login regression OK
  (bearer tokens), route surface unchanged — M010 adds no endpoints, so
  full live RBAC checks land with the first gated production route (M012+).
- Route-handler gates use the no-default `Annotated[User,
  Depends(require_role(...))]` style — a `Depends(...)` parameter *default*
  trips ruff B008 (see M009 note).
- Environment: the dev DB `users` table was found empty at verification
  (container recreated between sessions wiped non-volume data) — re-seeded
  `live-demo@example.com` for live checks.

---

### M011 — Farmer Profile Model & Migration

**Priority:** P0 **Depends On:** M008
**Status:** done

#### Objective
`farmers` table (hand-written Alembic revision `0003`) + `Farmer` ORM model:
the domain-facing profile for a farmer account, **1:1 with a `users` row**,
giving M012's CRUD API a subject and M013's farms a stable `farmer_id` to
reference.

#### Why This Milestone Exists
`users` (M008) is auth-only — email, password hash, role, is_active. Farmer
demographics (name, phone, village/district) and the surrogate `farmer_id`
that farms and oversight lists reference must not live in the auth table.
Separation keeps login/role concerns out of domain rows and lets
admins/officers exist without farmer profiles.

#### Files Expected to Be Created
- `src/models/farmer.py` (`Farmer` model)
- `alembic/versions/0003_farmers.py` (hand-written migration)
- `tests/models/test_farmer.py`

#### Files Expected to Be Modified
- `src/models/__init__.py` (export `Farmer` so `env.py`/autogenerate see it)
- `tests/test_migrations.py` (pinned revision `0002` → `0003`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
New table (revision `0003`, `down_revision = "0002"`):

```sql
farmers (
  id          uuid PRIMARY KEY,                -- app-side uuid4 (M008 style)
  user_id     uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  full_name   varchar(200) NOT NULL,
  phone       varchar(32)  NULL,
  village     varchar(120) NULL,
  district    varchar(120) NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
)
```

- `user_id` UNIQUE → the 1:1 constraint, also serving as the lookup index.
- `ON DELETE CASCADE`: deleting a user removes its profile (no orphan PII).
- Migration is **hand-written** (standing rule: never trust autogenerate;
  FK = `farmers_user_id_fkey`, unique = `farmers_user_id_key`).

#### API Changes
None (no endpoints in M011).

#### Frontend Changes
None.

#### External Dependencies
None.

#### Implementation Steps
1. Spec (here), roadmap row → in-progress.
2. `src/models/farmer.py`: `Farmer(Base)` mirroring `users` conventions
   (`Mapped`/`mapped_column`, tz-aware timestamps, `__repr__` with id +
   full_name only — no phone/location).
3. `alembic/versions/0003_farmers.py`: hand-written `upgrade`/`downgrade`
   (`drop_table("farmers")`), chained to `0002`.
4. Export `Farmer` from `src/models/__init__.py`.
5. Tests (`tests/models/test_farmer.py`, `_db` fixture pattern from
   `test_user.py`):
   - metadata: expected column set; `user_id` unique declared; FK to
     `users.id` with `ondelete="CASCADE"` declared.
   - integration: insert/select round trip with defaults (`phone`/`village`/
     `district` → NULL, timestamps set); duplicate `user_id` →
     `IntegrityError`; unknown `user_id` → `IntegrityError` (FK); delete
     user → farmer row gone (cascade).
6. Update `tests/test_migrations.py` pins to `0003`.

#### Acceptance Criteria
- [x] `alembic upgrade head` creates `farmers` at revision `0003`;
      `downgrade -1` drops it; full round-trip test green.
- [x] Model round-trips through Postgres with correct types and NULL
      defaults for optional columns.
- [x] DB enforces: one profile per user (unique), no orphan profiles (FK),
      cascade delete removes profile with user.
- [x] `Farmer` is importable from `src.models` (registered on
      `Base.metadata` — autogenerate would detect it).
- [x] Full quality gate green.

#### Unit Tests Required
- Metadata/column-set assertions and constraint declarations (no DB).

#### Integration Tests Required
- Insert/select round trip; unique/FK/cascade violations against real dev
  Postgres; migration upgrade→downgrade→base→upgrade at `0003`.

#### Security Checks Required
- [x] Cascade delete leaves no orphan personal data (profile rows cannot
      outlive their account).
- [x] `__repr__`/logs never include phone/village/district (PII) — id +
      full_name only.

#### Performance Checks Required
- [x] `user_id` UNIQUE constraint provides the 1:1 lookup index; no other
      hot-path impact (table not read by auth).

#### Memory/Resource Checks Required
None significant.

#### Failure Scenarios to Handle
- Second profile for the same user → `IntegrityError` from the DB.
- Profile for a nonexistent user → `IntegrityError` from the FK.
- Downgrade mid-life → `drop_table("farmers")` reversible (no data
  transformation involved).

#### Rollback Strategy
`alembic downgrade 0002` drops the table; `users` (M008) and auth (M009/
M010) unaffected. App code reverts by removing `src/models/farmer.py`.

#### Verification Commands
```bash
uv run pytest tests/models/test_farmer.py tests/test_migrations.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: alembic upgrade head / downgrade 0002 / upgrade head; inspect \d farmers
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No API endpoints (M012), no farms/plots (M013/M015), no phone-format or
name validation (that's M012's pydantic layer), no soft-delete/archival,
no demographics beyond the columns listed (YAGNI).

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 45 files OK,
  pytest **100 passed / 0 skipped** (8 new farmer: metadata column set,
  unique + FK-cascade declarations, repr-PII exclusion, round trip with
  NULL defaults, duplicate user_id → IntegrityError, orphan user_id →
  FK IntegrityError, cascade delete); bandit on `src/models` = 0 findings.
- Live on dev Postgres: `upgrade head` → `\d farmers` shows exactly the
  spec'd schema (incl. `farmers_user_id_key` UNIQUE and
  `farmers_user_id_fkey ... ON DELETE CASCADE`), `downgrade 0002` drops
  it ("no relation" confirmed), `upgrade` restores; `alembic current`
  = `0003 (head)`.
- `tests/test_migrations.py` revision pins updated 0002 → 0003.

---

### M012 — Farmer CRUD API

**Priority:** P0 **Depends On:** M011, M010
**Status:** done

#### Objective
`/api/v1/farmers` CRUD with the full authorization matrix on top of
M010's `require_role`/`CurrentUserDep`: farmers manage **their own**
profile, admins manage everything, extension officers read everything.

#### Why This Milestone Exists
First real domain API — it exercises auth (M009) + RBAC (M010) + the
farmer model (M011) together, establishes the ownership-check pattern
that M014/M016 reuse for farms/plots, and gives the dashboards (M047,
M052) data to render.

#### Files Expected to Be Created
- `src/api/v1/farmers.py` (schemas + router)

#### Files Expected to Be Modified
- `src/core/errors.py` (`Conflict` 409)
- `src/api/v1/__init__.py` (mount router)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None (reads/writes `farmers` from M011).

#### API Changes
All under `/api/v1/farmers`; list responses as
`{items: [...], total, limit, offset}`; farmer object =
`{id, user_id, full_name, phone, village, district, created_at, updated_at}`.

| Actor | POST | GET list | GET one | PATCH | DELETE |
|---|---|---|---|---|---|
| anonymous | 401 | 401 | 401 | 401 | 401 |
| farmer, own profile | 201 (self) | 403 | 200 | 200 | 403 |
| farmer, other's | 403 (mismatched user_id) | 403 | 404 | 404 | 404 |
| extension_officer | 403 | 200 | 200 | 403 | 403 |
| admin | 201 (any farmer-user) | 200 | 200 | 200 | 200 |

- **POST** (admin): body `user_id` must reference an existing user with
  `role=farmer` (missing user → 404, wrong role → 409, already has a
  profile → 409). **POST** (self, role=farmer): `user_id` forced to own id;
  provided `user_id` different from own → 403; already has profile → 409.
  Returns 201.
- **GET list**: `limit` (default 50, max 100), `offset` (>=0).
- **Ownership**: a farmer can read/update only profiles whose `user_id`
  equals theirs — non-owned → **404** (no existence leak); owned but
  forbidden action → **403**.
- **PATCH**: partial body, at least one field; `full_name` 1–200,
  `phone` loose `^\+?[0-9()\s-]{5,32}$`, `village`/`district` ≤120.
- **DELETE**: admin only; also removes the row (its `users` account and
  auth tokens are untouched — cascade runs the other direction).

#### Frontend Changes
None.

#### External Dependencies
None.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/core/errors.py`: `Conflict` (409 `conflict`).
3. `src/api/v1/farmers.py`: `FarmerCreate`/`FarmerPatch`/`FarmerRead`
   pydantic schemas; router with the five endpoints; helper
   `_get_authorized_farmer(session, farmer_id, user)` → row or
   404/403 per matrix; role checks via `require_role`, ownership via
   `user_id == current_user.id`.
4. Mount in `src/api/v1/__init__.py` (tag `farmers`).
5. Tests `tests/api/test_farmers.py` (own `_db`/seeded-users fixtures):
   see lists below.

#### Acceptance Criteria
- [x] Full matrix above passes against real dev Postgres.
- [x] Anonymous requests to every endpoint → 401 (before any role logic).
- [x] Farmer cannot read/modify/delete another farmer's profile (404) and
      cannot create for someone else (403).
- [x] Admin can create only for existing `role=farmer` users without a
      profile (404/409 otherwise).
- [x] PATCH validates field rules; empty patch → 422.
- [x] List pagination bounded (limit max 100) and admin/officer-only.
- [x] Full quality gate green.

#### Unit Tests Required
- Schema validation: full_name bounds, phone pattern, empty-patch
  rejection, limit clamp (no DB).

#### Integration Tests Required
- The complete matrix (anonymous/farmer-self/farmer-other/officer/admin ×
  five endpoints) + 409 duplicate-profile + admin wrong-role target +
  admin missing-user target, against dev Postgres.

#### Security Checks Required
- [x] 401 strictly precedes role/ownership checks.
- [x] Ownership enforced in the query path (lookup by id **and**
      authorization), never client-supplied filters.
- [x] Non-owned resources → 404 (no IDOR existence oracle) — logged for
      M017's cross-resource audit.
- [x] Validation rejects oversized/invalid fields before the DB.

#### Performance Checks Required
- [x] List = one SELECT + one COUNT; single-row paths = one SELECT;
      no N+1.

#### Memory/Resource Checks Required
None significant (per-request session).

#### Failure Scenarios to Handle
- Duplicate profile → 409, no partial rows.
- Target user missing / wrong role at create → 404 / 409, clean bodies.
- Concurrent creates for the same user → second commit hits the
  `user_id` UNIQUE constraint → 409 (IntegrityError mapped).
- Malformed UUID in path → FastAPI 422 (existing handler shape).

#### Rollback Strategy
Remove `src/api/v1/farmers.py` + router mount; `farmers` table (M011)
unaffected.

#### Verification Commands
```bash
uv run pytest tests/api/test_farmers.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: curl matrix with admin/farmer/officer tokens
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No user/registration endpoints (accounts stay seed-created), no bulk
import/export, no soft-delete, no farm/plot linkage (M013+), no listing
of user accounts (only farmer profiles).

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 47 files OK,
  pytest **115 passed / 0 skipped** (15 new: schema validation ×2, anon
  401 sweep, self-create/read, cross-create 403, duplicate 409, admin
  create 201/404/409-wrong-role, officer create 403, list matrix +
  bounds 422, get matrix, patch matrix, delete matrix);
  bandit on `src/api` + `errors.py` = 0 findings.
- Live matrix (uvicorn + dev DB) **12/12 exactly per spec table**:
  self-create 201, anon 401, owner-GET 200, other-GET 404, officer-GET
  200, officer-PATCH 403, other-PATCH 404, admin-PATCH 200, officer-list
  total=1, farmer-list 403, admin-DELETE 204, GET-after-delete 404.
- **Finding (data loss):** `tests/test_migrations.py`'s round-trip runs
  `downgrade base` → **reinitializes the whole schema after every gate
  run**, destroying all seeded dev accounts (this caused the confusing
  mid-verification 401s/405s). Rule: seed demo users **after the final
  gate run**, never before.
- **Finding (fixed):** `tests/models/test_farmer.py` teardowns used
  unscoped `DELETE FROM users` (wiped every account); now scoped to
  seeded ids (FK cascade cleans farmer rows). Same hygiene verified in
  the other fixtures.

---

### M013 — Farm Model & Migration (PostGIS geometry)

**Priority:** P0 🔒 (checkpoint **satisfied 2026-09-27**: human chose
PostGIS `geometry` column over GeoJSON-in-JSONB and over a plain point —
decision D7) **Depends On:** M011
**Status:** done

#### Objective
`farms` table (hand-written Alembic revision `0004`, `CREATE EXTENSION
postgis`) + `Farm` ORM model with a real PostGIS `geometry(Geometry, 4326)`
column for field boundaries, giving M014's CRUD API and the farm digital
twin (M018+) a spatially-queryable subject.

#### Why This Milestone Exists
Farms are the anchor of the whole digital twin: plots (M015) hang off
farms, and weather/satellite/soil overlays (M023+) need real spatial
queries (`ST_Intersects` etc.), which JSONB coordinates cannot express
efficiently. The human checkpoint chose a true spatial type over the
roadmap's original JSONB wording (D7).

#### Files Expected to Be Created
- `src/models/farm.py` (`Farm` model)
- `alembic/versions/0004_farms.py` (hand-written migration)
- `tests/models/test_farm.py`

#### Files Expected to Be Modified
- `docker-compose.yml` (db image `postgres:16` → `postgis/postgis:16-3.4`)
- `pyproject.toml` / `uv.lock` (add pinned `geoalchemy2`)
- `src/models/__init__.py` (export `Farm`)
- `tests/test_migrations.py` (pins `0003` → `0004`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
Revision `0004` (`down_revision = "0003"`):

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

farms (
  id            uuid PRIMARY KEY,                 -- app-side uuid4
  farmer_id     uuid NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
  name          varchar(120) NOT NULL,
  area_hectares numeric(10,2) NULL,
  geo           geometry(Geometry, 4326) NULL,    -- WGS84 boundary, GIST index
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE (farmer_id, name)                        -- no duplicate names per farmer
)
```

- `geo` NULL-able: profiles can be created before boundaries are mapped.
- Generic `Geometry` SRID 4326 (Polygon/MultiPolygon both storable);
  point-level validation of GeoJSON payloads happens at the API (M014).
- Spatial GIST index auto-created by GeoAlchemy2 (`spatial_index=True`).
- `ON DELETE CASCADE`: deleting a farmer profile removes its farms.
- Extension created by the migration (idempotent `IF NOT EXISTS`);
  `downgrade` drops the table and leaves the extension (harmless,
  re-created idempotently on upgrade).

#### API Changes
None (no endpoints in M013).

#### Frontend Changes
None.

#### External Dependencies
- `geoalchemy2` (pinned exact, adds to pyproject) — SQLAlchemy geometry
  type + `WKTElement`/EWKB handling; works via `asyncpg` (round-trip
  test proves it on this milestone).
- Docker image `postgis/postgis:16-3.4` (same PG16 major as before — the
  named volume `agrin_pgdata` keeps its data).

#### Implementation Steps
1. Spec (here), roadmap → in-progress, D7 recorded.
2. `docker-compose.yml` image swap; `docker compose up -d db` (recreates
   container, volume preserved); confirm `SELECT postgis_full_version()`.
3. `uv add geoalchemy2` → normalize to exact `==` pin in pyproject.
4. `src/models/farm.py`: `Farm(Base)` — uuid PK, `farmer_id` FK
   cascade, name, area_hectares, `Geometry(Geometry, srid=4326,
   spatial_index=True)`, tz timestamps, unique `(farmer_id, name)`,
   repr without geo blob.
5. `alembic/versions/0004_farmers.py`: hand-written — extension + table.
6. Export `Farm` from `src/models/__init__.py`.
7. Tests `tests/models/test_farm.py` (`_db` fixture pattern):
   - metadata: column set, unique `(farmer_id, name)`, FK cascade,
     SRID 4326 declared.
   - integration: extension present; insert farm with WKT polygon →
     `ST_AsText` round trip; duplicate (farmer, name) → IntegrityError;
     unknown farmer_id → FK IntegrityError; delete farmer → cascade.
8. `tests/test_migrations.py` pins → `0004`.

#### Acceptance Criteria
- [x] Dev DB runs PostGIS (`postgis_full_version()` works) after image swap.
- [x] `alembic upgrade head` → revision `0004`, `farmers`+`farms` both
      present; `downgrade 0003` drops `farmers` only; round-trip green.
- [x] Polygon writes/reads back identically (`ST_AsText` equality) —
      proves asyncpg + GeoAlchemy2 path.
- [x] DB enforces unique farm name per farmer, FK/cascade, SRID 4326.
- [x] Full quality gate green.

#### Unit Tests Required
- Metadata assertions (column set, SRID, unique key, FK) — no DB.

#### Integration Tests Required
- Extension availability, geometry round trip, unique/FK/cascade
  violations against real dev Postgres; migration round trip at `0004`.

#### Security Checks Required
- [x] `__repr__`/logs never dump the geo blob (can be large).
- [x] Extension creation is idempotent (no superuser surprises on rerun).

#### Performance Checks Required
- [x] GIST spatial index exists on `geo` (GeoAlchemy2 default) for
      M018+/overlay queries; no auth-path impact.

#### Memory/Resource Checks Required
None significant; large boundaries kept NULL until provided (no default
geometry).

#### Failure Scenarios to Handle
- PostGIS image not running → migration `CREATE EXTENSION` fails loudly
  (skip-if-unreachable fixture keeps gate green without Docker).
- Duplicate farm name for same farmer → `IntegrityError` (M014 maps → 409).
- Farm for deleted farmer → FK `IntegrityError` / cascade cleanup.

#### Rollback Strategy
`alembic downgrade 0003` (drops `farms`, extension stays); revert
`docker-compose.yml` image to `postgres:16` only on a fresh volume
(PostGIS-typed data would not load into vanilla Postgres).

#### Verification Commands
```bash
uv run pytest tests/models/test_farm.py tests/test_migrations.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: SELECT postgis_full_version(); \d farms ; round-trip ST_AsText
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No API endpoints (M014), no plots (M015), no GeoJSON payload validation
(M014's pydantic layer), no raster/tile serving, no projections other
than WGS84 (SRID 4326).

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 50 files OK,
  pytest **126 passed / 0 skipped** (11 new farm: metadata column set,
  unique(farmer_id,name), FK cascade, SRID/geometry-type, repr-no-geo,
  PostGIS extension live, WKT→`ST_AsText` exact round trip + `ST_SRID`
  4326, duplicate-name IntegrityError, cross-farmer same-name OK, FK
  IntegrityError, cascade delete); bandit on `src/models` + migration = 0.
- Live: `alembic current = 0004 (head)`; downgrade 0003 drops `farmers`
  only (extension + farmers intact); `\d farms` matches spec incl.
  `geo geometry(Geometry,4326)`, `idx_farms_geo` GIST, unique key, FK
  `ON DELETE CASCADE`; `postgis_version()` = 3.4.
- **asyncpg + GeoAlchemy2 round trip proven** (WKTElement bind →
  ST_AsText equality) — the main technical risk of D7 cleared.
- Container swap `postgres:16 → postgis/postgis:16-3.4` kept the named
  volume (same PG major); existing data needed an explicit
  `CREATE EXTENSION` (image init scripts only run on fresh volumes) —
  the migration owns this idempotently. Also ran
  `ALTER DATABASE agrin REFRESH COLLATION VERSION` (image glibc older
  than the one that created the data).

---

### M014 — Farm CRUD API + Ownership Authorization

**Priority:** P0 **Depends On:** M013, M010
**Status:** done

#### Objective
`/api/v1/farms` CRUD with GeoJSON boundary payloads (`ST_GeomFromGeoJSON`
in, `ST_AsGeoJSON` out) and the ownership matrix reused from M012:
farmers manage farms **of their own profile**, admins everything, officers
read everything.

#### Why This Milestone Exists
First spatial API — it proves the D7 stack end-to-end (GeoJSON → PostGIS →
GeoJSON), establishes farm ownership rules that M015 (plots) and M017
(IDOR audit) build on, and feeds the dashboards (M047) and farm-state
engine (M019).

#### Files Expected to Be Created
- `src/api/v1/farms.py` (schemas + router)

#### Files Expected to Be Modified
- `src/api/v1/__init__.py` (mount router)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None (uses `farms` from M013).

#### API Changes
All under `/api/v1/farms`; list envelope `{items, total, limit, offset}`;
farm object `{id, farmer_id, name, area_hectares, geo, created_at,
updated_at}` where `geo` is a GeoJSON Polygon/MultiPolygon (or null).

| Actor | POST | GET list | GET one | PATCH | DELETE |
|---|---|---|---|---|---|
| anonymous | 401 | 401 | 401 | 401 | 401 |
| farmer, own farm | 201 (own profile forced) | 200 (own only) | 200 | 200 | 403 |
| farmer, other's | 403 (profile mismatch) / 404 | scoped | 404 | 404 | 404 |
| extension_officer | 403 | 200 (all) | 200 | 403 | 403 |
| admin | 201 (any farmer profile) | 200 (all) | 200 | 200 | 200 |

- **POST** (farmer): `farmer_id` forced to own profile (mismatch → 403);
  no profile yet → 409 `conflict` ("create your farmer profile first").
  **POST** (admin): body `farmer_id` must exist (404 otherwise). Duplicate
  name for the same farmer → 409 (UNIQUE mapped from IntegrityError).
- **GET list**: farmer → auto-scoped to own `farmer_id`; admin/officer →
  all, optional `farmer_id` filter; `limit` 1–100 (default 50),
  `offset` ≥ 0.
- **Ownership**: non-owner farmer on get/patch/delete → **404**;
  officer read-only (patch/delete → 403); owner delete → 403; admin all.
- **PATCH**: ≥1 field; name ≤120, area ≥ 0, geo re-validated; partial
  updates never touch `farmer_id` (ownership is immutable).
- **Geo validation (pydantic)**: `type` ∈ {Polygon, MultiPolygon}; rings
  ≥ 4 positions, first == last; lon ∈ [-180,180], lat ∈ [-90,90];
  invalid → 422 before any DB write. Stored via
  `ST_GeomFromGeoJSON(json.dumps(...))`; read back via `ST_AsGeoJSON` in
  the same SELECT (no N+1).

#### Frontend Changes
None.

#### External Dependencies
None new (`geoalchemy2` from M013).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/api/v1/farms.py`: `GeoJsonPolygon`-style validator, `FarmCreate`
   / `FarmPatch` / `FarmRead` / `FarmList`; ownership helpers resolving
   `farm.farmer_id → farmer.user_id == current_user.id`; geo written with
   `func.ST_GeomFromGeoJSON`, read with `func.ST_AsGeoJSON`.
3. Mount in `src/api/v1/__init__.py` (tag `farms`).
4. Tests `tests/api/test_farms.py` (seeded farmer/officer/admin, minted
   tokens as in M012): matrix + geo validation + API geo round trip.

#### Acceptance Criteria
- [x] Full matrix above passes on real dev Postgres.
- [x] GeoJSON round trip through the API: POST polygon → GET returns the
      same coordinates; invalid ring/coords → 422, nothing persisted.
- [x] Farmer list auto-scoped (cannot see other farmers' farms); non-owner
      get/patch → 404.
- [x] Duplicate name per farmer → 409; farmer without profile → 409;
      admin unknown farmer_id → 404.
- [x] `farmer_id` immutable via PATCH.
- [x] Full quality gate green.

#### Unit Tests Required
- GeoJSON validator: valid polygon passes, open ring rejected, bad
  coordinates/`type` rejected, empty-patch rejected, area < 0 rejected
  (no DB).

#### Integration Tests Required
- Complete actor × endpoint matrix, API geo round trip (`ST_AsGeoJSON`
  equality), 409s, against dev Postgres.

#### Security Checks Required
- [x] 401 before role/ownership logic; ownership resolved server-side via
      `farmers.user_id` (never client filters).
- [x] Non-owner farmers get 404 (no existence oracle) — M017 input.
- [x] GeoJSON depth/size sane-guards (max coordinates length) so a huge
      payload cannot wedge PostGIS.

#### Performance Checks Required
- [x] List = one SELECT (incl. `ST_AsGeoJSON` per row) + one COUNT;
      single-row paths = one SELECT; no N+1.

#### Memory/Resource Checks Required
None significant (payload size capped by pydantic limits).

#### Failure Scenarios to Handle
- Concurrent duplicate name → second commit hits UNIQUE → 409.
- Malformed geometry reaching PostGIS despite validation → clean 422/409
  path, never 500 (validated pre-write).
- Farmer deleted under an open form → FK cascade (M013) — subsequent
  GETs → 404.

#### Rollback Strategy
Remove `src/api/v1/farms.py` + router mount; `farms` table (M013)
unaffected.

#### Verification Commands
```bash
uv run pytest tests/api/test_farms.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: curl matrix + polygon POST/GET round trip
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No plot linkage (M015), no area auto-computation from geometry
(`area_hectares` stays client-provided for now), no map/tile rendering,
no projection transforms (all WGS84).

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 52 files OK,
  pytest **141 passed / 0 skipped** (15 new: 3 pure-pydantic GeoJSON +
  patch validation, 12 API matrix/round-trip); bandit on
  `src/api/v1/farms.py` = 0 findings (replaced post-commit `assert`s with
  defensive `NotFound` raises for B101).
- **Live uvicorn matrix 30/30** (`live_m014.py`): 401s, farmer self
  create + geo round trip equality, farmer_id forced to own profile,
  cross-profile 403, no-profile 409, officer create 403, admin create +
  duplicate 409 + unknown farmer 404, bad geo 422, per-role list
  scoping (1/1/2 + filter), read matrix (200/200/404), patch matrix
  (404/403/200/200) + `farmer_id` immutability, delete matrix
  (403/403/404/204) + GET-after-delete 404.
- Numeric(10,2) serializes fixed-scale strings (`"1.50"`, `"9.00"`) —
  API contract note for frontend (M050+).
- `ST_AsGeoJSON` output compared with structural equality: JSON numeric
  equality (`0 == 0.0`) makes int/float rendering differences invisible.
- List path = ≤3 queries regardless of row count (profile lookup for
  farmers only + COUNT + page SELECT with per-row `ST_AsGeoJSON`) — no
  N+1 confirmed by construction.
- **Operational lesson:** live-verification rows (profiles/farms) left in
  the dev DB break `tests/api/*` (they run BEFORE `test_migrations`'s
  downgrade-base wipe) — clean live artifacts (scoped deletes) before
  re-running the gate; the gate's own end-of-suite wipe then leaves a
  clean head for demo seeding.

---

### M015 — Plot Model & Migration

**Priority:** P0 **Depends On:** M013
**Status:** done

#### Objective
`plots` table (Alembic rev `0005`): subdivision boundaries inside a farm,
same D7 geometry treatment as `farms`. Model + migration only — no API.

#### Why This Milestone Exists
Plots are the operating unit of the platform: M016 exposes them, M018/M019
attach crop state, M025+ drive overlays per plot. Schema-first keeps M016
pure CRUD work.

#### Files Expected to Be Created
- `src/models/plot.py`
- `alembic/versions/0005_plots.py`
- `tests/models/test_plot.py`

#### Files Expected to Be Modified
- `src/models/__init__.py` (export `Plot`)
- `tests/test_migrations.py` (pin `0005`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
New table `plots`:
- `id` uuid PK (client-side uuid4)
- `farm_id` uuid NOT NULL FK → `farms(id)` ON DELETE CASCADE, btree
  index `ix_plots_farm_id` (list-by-farm + cascade checks)
- `name` varchar(120) NOT NULL, `UNIQUE (farm_id, name)` →
  `plots_farm_id_name_key`
- `area_hectares` numeric(10,2) NULL (client-provided for now; M018 may
  derive from geometry)
- `geo` `geometry(Geometry, 4326)` NULL, GIST index
- `created_at`/`updated_at` timestamptz NOT NULL, `now()` defaults

No API changes, no frontend changes, no new dependencies.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `Plot` model mirroring `Farm` (PII-free repr, no geo blob in repr).
3. Hand-written `0005_plots.py` (standing rule: never autogenerate;
   GeoAlchemy2 hook emits the GIST index).
4. Export + migration pin.
5. `tests/models/test_plot.py`: metadata assertions (no DB) + integration
   (round trip, uniqueness scope, FK, cascade).

#### Acceptance Criteria
- [x] `alembic current = 0005 (head)`; `downgrade 0004` drops `plots`
      only; round-trip green; `farms`/`farmers` untouched.
- [x] Unique plot name **per farm** enforced; same name in another farm
      OK; unknown `farm_id` rejected; deleting a farm removes its plots.
- [x] Geometry round trip exact (`ST_AsText` equality) + SRID 4326;
      `ix_plots_farm_id` and GIST `idx_plots_geo` present.
- [x] Full quality gate green.

#### Unit Tests Required
Metadata: column set, unique scope, FK cascade, SRID, `farm_id` index,
repr without geo blob.

#### Integration Tests Required
Geometry round trip; duplicate `(farm_id, name)` IntegrityError;
cross-farm same-name OK; orphan `farm_id` IntegrityError; farm→plots
cascade.

#### Security Checks Required
- [x] Repr/logs never dump geo blob (large polygons).
- [x] Cascade cannot orphan plots or leak across farms.

#### Performance Checks Required
- [x] `ix_plots_farm_id` btree for M016 list queries; GIST for M018+
      overlays.

#### Memory/Resource Checks Required
None (schema only).

#### Failure Scenarios to Handle
- Concurrent duplicate `(farm_id, name)` → UNIQUE → IntegrityError
  (mapped to 409 in M016).
- Upgrading from `0004` must not require the extension re-create
  (0004 owns it) — 0005 stays extension-free.

#### Rollback Strategy
`alembic downgrade 0004` drops `plots`; nothing else references it yet.

#### Verification Commands
```bash
uv run pytest tests/models/test_plot.py tests/test_migrations.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: alembic current/downgrade/upgrade + \d plots
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No API endpoints (M016), no crop/stage/planting-date columns (M018),
no spatial containment validation (plot within farm) — that belongs to
M016's service layer, no area computation from geometry.

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 55 files OK,
  pytest **152 passed / 0 skipped** (11 new plot: 6 metadata incl. btree
  index + 5 integration incl. WKT round trip and farm→plots cascade);
  bandit on `src/models` + 0005 migration = 0 findings.
- Live: `alembic current = 0005 (head)`; downgrade `0004` drops `plots`
  only (`farms` intact); `\d plots` matches spec exactly —
  `geometry(Geometry,4326)`, `idx_plots_geo` GIST, `ix_plots_farm_id`
  btree, `plots_farm_id_name_key` unique, FK `ON DELETE CASCADE`.

---

### M016 — Plot CRUD API + Ownership Authorization

**Priority:** P0 **Depends On:** M015, M010
**Status:** done

#### Objective
`/api/v1/farms/{farm_id}/plots` CRUD (nested routes) with GeoJSON
payloads, reusing M014's farm authorization helper and adding the
**plot-within-farm containment check** deferred from M015
(`ST_Covers(farm.geo, plot.geo)`).

#### Why This Milestone Exists
Completes the spatial data entry path (farm → plot), unlocks M017's
cross-resource IDOR audit, and is the write side of everything M018+
reads.

#### Files Expected to Be Created
- `src/api/v1/plots.py` (schemas + router)
- `tests/api/test_plots.py`

#### Files Expected to Be Modified
- `src/api/v1/__init__.py` (mount router, tag `plots`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None (uses `plots` from M015).

#### API Changes
Nested under `/api/v1/farms/{farm_id}/plots`; plot object
`{id, farm_id, name, area_hectares, geo, created_at, updated_at}`;
list envelope `{items, total, limit, offset}`.

| Actor | POST | GET list | GET one | PATCH | DELETE |
|---|---|---|---|---|---|
| anonymous | 401 | 401 | 401 | 401 | 401 |
| farmer, own farm | 201 | 200 (own farm only) | 200 | 200 | 403 |
| farmer, other's | 404 | 404 | 404 | 404 | 404 |
| extension_officer | 403 | 200 | 200 | 403 | 403 |
| admin | 201 | 200 | 200 | 200 | 200 |

- Authorization for every endpoint starts with M014's
  `_authorized_farm` on the URL's `farm_id` (non-owner farmer → 404,
  no oracle) — plots inherit the parent farm's ownership rules.
- Plot lookup is scoped `WHERE id = plot_id AND farm_id = farm_id` →
  a plot id from another farm → 404 (never leaks cross-farm).
- Duplicate plot name **within the farm** → 409; same name in another
  farm → 201 (DB unique scope does the work).
- **Containment (M015 deferral):** when both `plot.geo` is provided and
  the parent farm has a non-NULL boundary, `ST_Covers` must be true or
  the request → 422 (`validation_failed`, nothing persisted). Farm
  boundary NULL → check skipped (cannot enforce what isn't mapped).
- Reuses `PlotCreate`/`PlotPatch`-style pydantic validation from
  `src/api/v1/farms.py` (`_validate_geojson`, ≥1-field patch,
  numeric(10,2) area, immutable `farm_id`).

#### Frontend Changes
None.

#### External Dependencies
None new.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/api/v1/plots.py`: import `_validate_geojson`, `_row_to_read`
   pattern, and `_authorized_farm` from `.farms`; containment helper via
   one `SELECT ST_Covers(...)`; mount.
3. `tests/api/test_plots.py`: matrix + containment + geo round trip
   (fixtures seed users/profiles/farms directly, scoped cleanup).

#### Acceptance Criteria
- [x] Full matrix above passes on real dev Postgres.
- [x] GeoJSON round trip through the API; invalid geo → 422.
- [x] Plot outside farm boundary → 422 with nothing persisted; inside →
      201; unmapped farm accepts any valid geo.
- [x] Duplicate `(farm_id, name)` → 409; cross-farm plot id → 404;
      non-owner farmer → 404 on every verb.
- [x] Full quality gate green.

#### Unit Tests Required
- Empty `PlotPatch` → ValidationError; geo validator reuse covered via
  API 422 path (already unit-tested in M014).

#### Integration Tests Required
- Complete actor × endpoint matrix against dev Postgres; containment
  pass/fail/skip cases; API geo round trip.

#### Security Checks Required
- [x] 401 before role/ownership logic; parent-farm authz resolved
      server-side (M017 input).
- [x] Cross-farm plot ids → 404 (no existence oracle).
- [x] GeoJSON size guard inherited (`MAX_GEOJSON_CHARS`).

#### Performance Checks Required
- [x] List = parent authz (1) + COUNT (1) + page SELECT (1) — constant
      regardless of plot count; single ops ≤ 4 queries (authz, plot row,
      optional ST_Covers, write).

#### Memory/Resource Checks Required
None significant (payload cap inherited).

#### Failure Scenarios to Handle
- Concurrent duplicate `(farm_id, name)` → IntegrityError → 409.
- Farm boundary changed after plots exist (M014 could shrink it) →
  revalidation of existing plots is NOT this milestone (documented
  below); only incoming plot writes are checked.
- Malformed geometry → 422 pre-write; containment check never sees it.

#### Rollback Strategy
Remove `src/api/v1/plots.py` + router mount; `plots` table (M015)
unaffected.

#### Verification Commands
```bash
uv run pytest tests/api/test_plots.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: curl matrix + containment cases
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No area computation from geometry, no revalidation of existing plots
when a farm boundary shrinks (future: farm-state/service work), no
crop/stage fields (M018), no plot-in-plot or MultiPolygon containment
refinements beyond `ST_Covers`.

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy 57 files OK,
  pytest **165 passed / 0 skipped** (13 new plot-API); bandit on
  `src/api/v1/plots.py` = 0 findings.
- **Live uvicorn matrix 29/29** (`live_m016.py`): 401s, owner create +
  geo round trip, containment 422 (outside) / skip (unmapped farm),
  stranger 404 ×5, officer read-only (403/200/403/403), admin full,
  dup-name 409 scoped per farm, cross-farm plot id 404, patch matrix +
  rejected geo leaves boundary untouched, delete matrix, and live
  artifact cleanup (farms + profiles deleted before the final gate —
  M014 lesson applied).
- Containment runs as one `SELECT ST_Covers(farm.geo, ST_GeomFromGeoJSON(...))`
  — NULL farm boundary yields NULL → treated as "skip" (cannot enforce
  what isn't mapped); `covered is False` → 422 pre-write.

---

### M017 — Cross-resource authorization audit (IDOR pass)

**Priority:** P0 **Depends On:** M012, M014, M016
**Status:** done

#### Objective
A single cross-cutting audit of every `/api/v1` surface built so far
(farmers, farms, plots, auth): a **route-inventory default-deny test**
against the real app, a **cross-tenant IDOR matrix** with
oracle-equivalence assertions, **mass-assignment (field-immutability)**
probes, and **list-scoping** checks — plus fixes for anything the audit
finds.

#### Why This Milestone Exists
M012/M014/M016 each tested their own resource in isolation; nobody has
yet asserted authorization *across* resources as a system, nor that no
route accidentally became public. This is the last P0 gate of the
Farmer/Farm/Plot domain before the Farm Digital Twin (M018+) starts
reading it.

#### Files Expected to Be Created
- `tests/api/test_idor.py` (the audit suite)

#### Files Expected to Be Modified
- `MILESTONES.md`, `ENGINEERING_STATE.md`
- `src/api/v1/*.py` / `src/api/deps.py` — **only if the audit finds a
  defect** (no speculative changes; each fix logged in Notes below)

#### Database Changes
None.

#### API Changes
None intended. Any change found necessary must preserve the documented
status-code contract below.

#### Frontend Changes
None.

#### External Dependencies
None new.

#### Audit Scope (the contract being verified)

**Public allow-list (anonymous access is correct here, nothing else):**
`GET /`, `GET /health`, `GET /ready`, `GET /docs`, `GET /redoc`,
`GET /openapi.json`, `GET /api/v1/ping`, `POST /api/v1/auth/login`,
`POST /api/v1/auth/refresh`. Every other registered route must 401 for
an anonymous caller.

**Cross-tenant status-code contract (per resource, both actors `farmer`):**

| Scenario | Expected |
|---|---|
| alpha → bravo's farmer profile (GET/PATCH/DELETE) | 404 |
| alpha → random nonexistent profile id | 404, **body identical** to the non-owned case |
| alpha → bravo's farm (GET/PATCH/DELETE) | 404, body identical to nonexistent-farm |
| bravo → alpha's plot via alpha's farm URL | 404 (parent-farm authz first) |
| bravo → alpha's plot id via **bravo's own** farm URL | 404, body identical to random plot id in that farm |
| officer → existing resource, write verb | 403 (officers can read, so existence is not a leak) |
| officer → nonexistent resource, any verb | 404 (row check runs first — no behavioral change needed) |
| admin | full access everywhere |

**Mass assignment (immutable fields must ignore client input):**
`PATCH /farmers/{id}` cannot change `user_id` (or the linked user's
`role`/`email`/`password_hash`); `PATCH /farms/{id}` cannot change
`farmer_id`; `PATCH /farms/{id}/plots/{id}` cannot change `farm_id`.

**List scoping:** a farmer's `?farmer_id=<other>` filter on
`GET /api/v1/farms` must be ignored (auto-scoped to own profile);
`GET /api/v1/farmers` stays 403 for farmers; a farmer with **no**
profile gets an empty farm list (200) and a 409 on farm-create.

**Robustness:** malformed UUID in path/query → 422 (never 500);
anonymous callers get 401 **before** body/path validation wherever the
dependency chain allows (asserted, findings noted not "fixed" if ordering
differs — a 422 for anonymous is not a security hole, but record it).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. DISCOVER pass: enumerate `create_app().routes`; grep every route
   decorator for auth dependencies; confirm the allow-list above matches
   reality (any extra public route = finding).
3. Write `tests/api/test_idor.py` using the established fixture pattern
   (seed alpha/bravo/officer/admin + farm A/alpha with plots, farm
   B/bravo with a plot; scoped cleanup by user email; `_db` fixture
   skipping when Postgres is unreachable).
4. Run the suite; triage every failure as (a) test bug, or (b) real
   authorization defect → fix in `src/`, log it in Notes, re-run.
5. Full quality gate; live verification; docs + state + commit.

#### Acceptance Criteria
- [x] Route-inventory test: every non-allow-listed route of the **real**
      app returns 401 anonymously (no accidentally-public endpoint).
- [x] Cross-tenant matrix green: all non-owned farmer access → 404 with
      body byte-identical to the nonexistent-id case (no oracle).
- [x] Mass-assignment probes green: `user_id`/`role`/`farmer_id`/`farm_id`
      unchanged after PATCH attempts carrying them.
- [x] List-scoping probes green (including the no-profile farmer).
- [x] Malformed UUID → 422, never 500.
- [x] Full quality gate green; every finding fixed or explicitly
      documented as accepted with rationale.

#### Unit Tests Required
- (Covered by the API-level tests below; schema immutability is asserted
  through response + re-fetch rather than model units.)

#### Integration Tests Required
- The whole of `tests/api/test_idor.py` against the dev Postgres.

#### Security Checks Required (Section 9 items in scope)
- [ ] Authentication bypass / accidentally-public routes (inventory test).
- [ ] IDOR + authorization flaws (cross-tenant matrix, oracle equality).
- [ ] Mass assignment / excessive data exposure (immutable-field probes;
      response models are explicit Pydantic schemas — re-verify no model
      leaks `password_hash`).
- [ ] Missing input validation → 422 not 500 (malformed UUID probes).
- [ ] Sensitive data in error responses (assert error bodies carry only
      `error_code` + `message`).
- [ ] Rate-limit gaps on `POST /auth/login` — **flagged for M055**, not
      fixed here (out of M017 scope).

#### Performance Checks Required
- Audit tests are test-only; no production-path change expected. If a
  fix touches a query, re-check it stays ≤ the previous query count
  (authz stays one joined SELECT).

#### Memory/Resource Checks Required
None significant (test-only milestone unless a fix lands).

#### Failure Scenarios to Handle
- A route found public → treat as defect: add the auth dependency, note
  it in Notes, keep the inventory test as the regression guard.
- Fixture pollution across tests (established lesson: scope every delete
  to seeded rows).
- Inventory test hitting routes with path params → substitute a random
  UUID so 401 (not 422/500) is what's being measured.

#### Rollback Strategy
Test-only: delete `tests/api/test_idor.py` + revert the roadmap row. Any
src fix reverts independently (one commit per fix if one is needed).

#### Verification Commands
```bash
uv run pytest tests/api/test_idor.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No new endpoints, no schema changes, no rate limiting (M055), no
frontend, no refactors beyond defect fixes the audit forces.

#### Verification & Notes (added on completion)
- Gate PASSED: ruff format OK, ruff check OK, mypy OK, pytest
  **178 passed / 0 skipped** (+13 new IDOR tests); bandit on
  `tests/api/test_idor.py` = 0 medium/high (66 low = `assert` in test
  code, accepted); `pip-audit` = no known vulnerabilities.
- **Live uvicorn 8/8** (`live_m017.py` over real HTTP): anonymous
  inventory 15/15 non-public operations → 401, public allow-list
  reachable, live login ×2, cross-tenant GET 404 with oracle-free body,
  cross-tenant PATCH 404, mass-assignment PATCH 200 but DB owner
  unchanged, malformed UUID → 422.
- **No authorization defects found in `src/` — zero production-code
  changes.** The audit confirmed the M012/M014/M016 contract as designed:
  - Inventory is driven from the real app's OpenAPI schema (21
    operations; 6 API-public + 4 docs routes + `/` in the allow-list),
    so any future route missing its auth dependency fails
    `test_every_non_public_operation_requires_auth`.
  - Anonymous 401 fires **before** body and path-parameter validation on
    every operation (empirically asserted — dependency ordering holds).
  - Farm-create mismatch guard (farmer naming a foreign `farmer_id`)
    returns the same 403 whether the id exists or is random → no
    existence oracle.
- **Accepted observations (documented, not fixed):**
  1. Starlette's route-mismatch 404 (`{"detail": "Not Found"}`) has a
     different *shape* than app errors (`error_code`/`message`). Not a
     leak (both plainly mean not-found), but noted for M055 (optional
     `HTTPException` handler for shape unification).
  2. Officer sees 404 for a missing row vs 403 for an existing one —
     accepted: officers can already read every farm/profile, so nothing
     is revealed. Contract asserted in
     `test_officer_write_ordering_documents_no_new_oracle`.
  3. Login/refresh rate limiting remains flagged for **M055** (unchanged
     from M009).
- Two initial failures were **test bugs**, not defects: a comparison
  path missing the `/plots` segment, and asserting 403 on `GET /farms`
  (farmers legitimately list their own farms — the staff-only list is
  `GET /farmers`). Fixed and re-run to green.

---

### M018 — Farm State schema (crop, stage, planting date, signal cache)

**Priority:** P0 **Depends On:** M015
**Status:** done

#### Objective
Two tables (hand-written migration `0006`) that make the Farm Digital
Twin persistable: **`plot_states`** (what is growing where: crop,
growth stage, planting date — 1:1 with a plot) and
**`farm_signal_caches`** (latest external conditions per farm: a JSONB
`signals` document + `refreshed_at`).

#### Why This Milestone Exists
Everything from M019 onward (state service, health/risk/recommendation
engines, disease context, decision engine, dashboards) reads the crop
facts from here instead of recomputing them, and the ingestion services
(M023/M026/M029) need a designated place to publish their latest values.

#### Grain decision (documented data-model call, not flagged 🔒 in §6)
- **Crop/stage/planting date are per-plot**, not per-farm: a farm's
  plots routinely carry different crops, and M018's dependency on M015
  (Plot) — not M013 (Farm) — is the roadmap telling us the same thing.
  "Farm State" = the twin aggregate served from `plot_states` +
  `farm_signal_caches` together (M019 computes/queries it).
- **Signals are per-farm**: weather/NDVI/soil are fetched for the
  farm's location once, then shared by all its plots — one cache row
  per farm avoids redundant provider calls (perf checklist).

#### Files Expected to Be Created
- `src/models/plot_state.py`
- `src/models/farm_signal_cache.py`
- `alembic/versions/0006_farm_state.py` (hand-written)
- `tests/models/test_state.py`

#### Files Expected to Be Modified
- `src/models/__init__.py` (register/export models)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
`alembic` revision **0006** (down_revision `0005`), two tables:

```
plot_states
  plot_id     uuid PK → plots.id ON DELETE CASCADE   (enforces 1:1)
  crop        varchar(80)  NOT NULL
  growth_stage varchar(40) NOT NULL
              CHECK (growth_stage IN ('germination','vegetative',
                     'flowering','fruiting','maturation','harvest'))
  planted_on  date NOT NULL
  created_at / updated_at  timestamptz NOT NULL, server_default now()

farm_signal_caches
  farm_id     uuid PK → farms.id ON DELETE CASCADE
  signals     jsonb NOT NULL DEFAULT '{}'   -- {"weather": {...},
                                             --  "satellite": {...},
                                             --  "soil": {...}}
  refreshed_at timestamptz NOT NULL, server_default now()  -- source fetch time
  created_at / updated_at  timestamptz NOT NULL, server_default now()
```

- Cascade chain verified: delete farm → plots → plot_states; delete farm
  → farm_signal_caches.
- No GIN index on `signals`: the only access pattern is PK point lookup
  and whole-document read/write (documented as "not needed yet", re-check
  in M056 if a `@>` containment query ever appears).
- No `planted_on <= today` DB check: future planting dates are a
  legitimate plan (app-level validation belongs to M020's API).

#### API Changes
None (M020). The `GROWTH_STAGES` canonical tuple lives in
`src/models/plot_state.py` so M020/M054 share one source of truth.

#### Frontend Changes
None (M047/M048).

#### External Dependencies
None new.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Models + `__init__.py` exports.
3. Hand-written migration `0006` (standing rule: never trust
   autogenerate — but still diff it against autogenerate output as a
   cross-check).
4. `tests/models/test_state.py`: metadata assertions (no DB) +
   integration (DB): insert, 1:1 violation, JSONB round trip, cascades,
   stage CHECK enforcement, orphan FK rejection.
5. Gate (includes the global upgrade→downgrade→upgrade migration
   round-trip), live verify, docs, state, commit.

#### Acceptance Criteria
- [x] `alembic upgrade head` / `downgrade base` round-trip clean;
      `0006` hand-reviewed against autogenerate output (`alembic check`:
      "No new upgrade operations detected" after the `spatial_ref_sys`
      filter).
- [x] Duplicate `plot_states.plot_id` rejected by the DB (PK).
- [x] Unknown growth stage rejected by the DB (CHECK); unknown plot/farm
      id rejected by FK.
- [x] Deleting a farm removes its plots' states and its signal cache;
      deleting a plot alone removes only that plot's state.
- [x] JSONB `signals` round-trips exactly (nested keys, numbers, nulls).
- [x] Full quality gate green.

#### Unit Tests Required
- Table/column/constraint metadata assertions for both tables (no DB).
- `GROWTH_STAGES` contains the six CHECK values (test stays honest if
  either side changes).

#### Integration Tests Required
- Insert/read, 1:1 duplicate → IntegrityError, stage CHECK violation →
  IntegrityError, orphan FK → IntegrityError, farm/plot cascade
  behavior, JSONB round trip — all against dev Postgres.

#### Security Checks Required
- [ ] No secrets/PII in schema; `signals` content is provider data only
      (raw farmer records stay in their own tables).
- [ ] FK+cascade so no orphaned state rows can be served later without
      their parent (M020 must still authorize via the farm chain —
      noted as an M020 requirement).

#### Performance Checks Required
- [ ] Both tables are PK-addressed point lookups; no unbounded growth
      per request; no new query patterns in this milestone.

#### Memory/Resource Checks Required
None significant (schema only).

#### Failure Scenarios to Handle
- Migration applied twice → idempotent (Alembic; global round-trip test
  proves it).
- Autogenerate drops/misses the CHECK → hand-review + explicit test.
- Deleting a farm with states + caches in one transaction → no FK
  violation (cascade order proven by integration test).

#### Rollback Strategy
`alembic downgrade 0005` drops both tables; models revert with the
files.

#### Verification Commands
```bash
uv run pytest tests/models/test_state.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# live: alembic upgrade head / downgrade base / upgrade head + \d plot_states
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No state computation/query service (M019), no API (M020), no provider
ingestion writing into `signals` yet (M023+), no frontend, no GIN
indexes or partitioning.

#### Verification & Notes (added on completion)
- **Deviation (logged):** `alembic/env.py` modified — added an
  `include_object` filter excluding PostGIS's `spatial_ref_sys` from
  autogenerate diffs. Without it, `alembic check` (this milestone's
  cross-check step) always fails with a bogus `remove_table`, which
  would mask real drift in every future hand-reviewed migration.
- **Deviation (logged):** `tests/test_migrations.py` — the three
  hardcoded `== "0005"` head assertions broke on revision 0006 (they
  broke the same way at 0006's predecessors by design of the literal).
  Replaced with `_head_revision()` derived from Alembic's script
  directory so future milestones don't re-break this gate.
- Gate PASSED: ruff format OK, ruff check OK, mypy OK, pytest
  **192 passed / 0 skipped** (+14 state tests); bandit medium/high on
  all touched files = 0; `pip-audit` = no known vulnerabilities.
- **Live verification:** `alembic downgrade 0005` → both tables gone
  (`to_regclass` NULL), `upgrade head` → both present; `\d plot_states`
  shows PK `plot_id`, FK `plots.id ON DELETE CASCADE`, and the stage
  CHECK with exactly the six `GROWTH_STAGES` values (model, migration
  and constant provably aligned via
  `test_growth_stage_check_matches_growth_stages_constant`).
- Findings fixed during the milestone (both in test expectations, one
  revealing a real schema issue):
  1. Model did not declare the stage CHECK (only the migration did) —
     added `CheckConstraint` built from `GROWTH_STAGES` to
     `PlotState.__table_args__` so metadata, migration and constant
     cannot drift; `alembic check` now guards it.
  2. SQLAlchemy wraps zero-arg column defaults as `lambda ctx: fn()`
     — asserted via `wrapped(None) == {}` instead of identity.

---

### M019 — Farm State service (compute/query)

**Priority:** P0 **Depends On:** M018
**Status:** done

#### Objective
`src/services/farm_state.py`: async service functions that
**(a)** assemble the Farm Digital Twin view of a farm (plots + crop
state + days-since-planting + signal cache with age) in a constant
number of queries, and **(b)** provide the write paths (`set_plot_state`
upsert, `clear_plot_state`, `put_signals` upsert) that M020's API and
M054's seed script will call.

#### Why This Milestone Exists
M018 stored the tables; this milestone makes them *usable* — the single
read entry point M020 exposes and the single write path every later
milestone (ingestion M023/M026/M029, seed M054, engines M032+ via reads)
goes through, so query shape and derived fields stay consistent.

#### Files Expected to Be Created
- `src/services/farm_state.py`
- `tests/services/__init__.py`
- `tests/services/test_farm_state.py`

#### Files Expected to Be Modified
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None (tables exist from M018).

#### API Changes
None (M020). Service DTOs (`FarmStateView`, `PlotStateView`,
`SignalCacheView` — Pydantic) are defined here and **reused by M020**.

#### Frontend Changes
None.

#### External Dependencies
None new.

#### Service Contract
```python
async def get_farm_state(session, farm_id, *, now=None) -> FarmStateView
    # 3 queries: farm row, plots LEFT JOIN plot_states, signal cache.
    # Raises NotFound if the farm doesn't exist.
    # NO AUTHZ HERE — callers must authorize first (M020 uses M014's
    # _authorized_farm); documented loudly in the module docstring.

async def set_plot_state(session, plot_id, *, crop, growth_stage, planted_on)
    # Validates growth_stage against GROWTH_STAGES (ValidationFailed),
    # pre-checks plot existence (NotFound), then
    # INSERT ... ON CONFLICT (plot_id) DO UPDATE — idempotent upsert.

async def clear_plot_state(session, plot_id) -> None   # idempotent delete

async def put_signals(session, farm_id, *, signals, refreshed_at=None)
    # Pre-checks farm (NotFound), upserts the cache document wholesale
    # (last-writer-wins per provider family is M023+/M031's concern).
```

Derived fields computed in `get_farm_state` (deterministic, no I/O):
- `days_since_planted` = `(now.date() - planted_on).days`; negative =
  future planting date, exposed as-is (documented, not clamped);
  `None` for plots without state.
- `signals.age_seconds` = seconds since `refreshed_at`; `None` when the
  cache row doesn't exist (freshness *policy*/staleness thresholds are
  deliberately NOT decided here — engines decide in M032+).
- `crops` = sorted unique crop list across planted plots; summary
  counts (`plot_count`, `planted_plot_count`).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Service module with DTOs + the four functions (postgres
   `insert().on_conflict_do_update` for both upserts).
3. `tests/services/test_farm_state.py` against dev Postgres: read-view
   assembly (incl. a plot without state), days/age math with injected
   `now`, upsert idempotency (2 calls → 1 row, second wins), clear
   idempotency, NotFound paths, bad-stage ValidationFailed, query-count
   guard (3 queries for the read path — performance check).
4. Gate, live verify, docs, state, commit.

#### Acceptance Criteria
- [x] `get_farm_state` returns the full view (plots, states, summary,
      signals) in exactly 3 queries; unknown farm → `NotFound`.
- [x] `set_plot_state` twice → single row with second values; bad stage
      → `ValidationFailed` before any DB write; unknown plot →
      `NotFound`.
- [x] `put_signals` twice → single cache row, signals replaced wholesale;
      unknown farm → `NotFound`.
- [x] `clear_plot_state` on a plot with/without state → both succeed.
- [x] Full quality gate green.

#### Unit Tests Required
- DTO/derived-math tests with injected `now` (no I/O where practical);
  `GROWTH_STAGES` validation rejects an unknown stage.

#### Integration Tests Required
- All of the above against dev Postgres with real rows (seed/cleanup
  scoped to seeded users, house rule).

#### Security Checks Required
- [x] No authz claimed in the service — module docstring warning present
      (M020 must call `_authorized_farm` first; enforced by M020 tests).
- [x] No raw SQL string interpolation anywhere (ORM/`insert()` only).

#### Performance Checks Required
- [x] Read path = 3 queries regardless of plot count (asserted with a
      counted-execution test or documented measurement).
- [x] Upserts are single-statement (`ON CONFLICT`), no read-modify-write.

#### Memory/Resource Checks Required
None significant (bounded result sets: one farm's plots).

#### Failure Scenarios to Handle
- Concurrent upserts of the same plot state → `ON CONFLICT` makes the
  last writer win; no IntegrityError escape.
- Farm deleted between authz and read (M020 race) → `NotFound`.
- `refreshed_at` provided by ingestion in the past/future → stored as
  given; `age_seconds` may be negative (documented, not clamped).

#### Rollback Strategy
Delete the service file + tests; nothing else imports it until M020.

#### Verification Commands
```bash
uv run pytest tests/services/test_farm_state.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No HTTP layer (M020), no authorization (M020 via M014 helper), no
provider calls (M022+), no health/risk computation (M032/M033), no
staleness policy thresholds, no caching layer.

#### Verification & Notes (added on completion)
- Service delivered as spec'd: 4 functions + 3 Pydantic DTOs;
  `get_farm_state` runs exactly 3 queries (asserted via a
  `before_cursor_execute` listener filtered to farm/plot/cache table
  statements), both upserts are single-statement `ON CONFLICT`.
- Tests: 10 new (`tests/services/test_farm_state.py`) covering view
  assembly, empty-farm zeros, injected-`now` math incl. negative
  days/age (documented-as-is), query-count guard, upsert idempotency,
  validation/NotFound paths, idempotent clear, wholesale signal
  replace, Decimal area round-trip.
- **Incident:** the first (broken) test run crashed `_seed` after
  inserting rows but before the caller tracked the user id → 9 leaked
  seeds broke 4 unrelated tests in the next gate
  (`MultipleResultsFound` / wrong privileged-list totals). Fixes: seed
  now appends its user id to the caller's `seeded` list *inside*
  `_seed`, immediately after commit (partial-seed failures stay
  tracked); hardened two unscoped `select(Plot).where(Plot.name == ...)`
  reads in `tests/models/test_plot.py` to also filter by `farm_id`.
  DB was restored clean by the gate's migration round-trip.
- Deviations: none beyond the two test-hardening edits above.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **202
  passed** (192 baseline + 10 new); bandit `-r -ll` on
  `src/services` + `tests/services` = 0; pip-audit clean (only the
  local `agrin` package skipped, not on PyPI).
- Live (`live_m019.py` on dev DB 65432): insert+upsert → 1 row second
  values win, wholesale signal replace, full view (days_since_planted
  = 8, age_seconds = 0), both NotFound paths, bad-stage
  `ValidationFailed`, clear twice → 0 rows; cleanup deleted seeded
  rows. ALL PASS.

### M020 — Farm State API

**Priority:** P0 **Depends On:** M019, M010
**Status:** done

#### Objective
`src/api/v1/farm_state.py`: four endpoints wiring M019's service to
HTTP with M014's authorization matrix — read the Farm Digital Twin
view, set/clear a plot's crop state, push a farm's signal cache.

#### Why This Milestone Exists
M019's service has no HTTP surface; this milestone is what the demo
frontend (M055+) and API consumers actually call to see and edit the
twin. It also locks the authz story the M019 docstring deferred:
every route authorizes with `_authorized_farm` / `_authorized_plot`
*before* touching the service.

#### Files Expected to Be Created
- `src/api/v1/farm_state.py`
- `tests/api/test_farm_state.py`

#### Files Expected to Be Modified
- `src/api/v1/__init__.py` (router registration)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None.

#### API Changes
All under `/api/v1`, tag `farm-state`:

| Method | Path | Authz | Success |
|---|---|---|---|
| GET | `/farms/{farm_id}/state` | read matrix (officer OK) | 200 `FarmStateView` |
| PUT | `/farms/{farm_id}/plots/{plot_id}/state` | write matrix (owner/admin; officer 403; non-owner 404) | 204 |
| DELETE | `/farms/{farm_id}/plots/{plot_id}/state` | write matrix | 204 |
| PUT | `/farms/{farm_id}/signals` | write matrix | 204 |

- Response body of GET reuses the service DTO `FarmStateView` directly
  (M019 contract).
- Request `PUT plot state`: `{crop, growth_stage, planted_on}` —
  `growth_stage` is a `Literal[*GROWTH_STAGES]` (pydantic → 422),
  `crop` min 1 / **max 80** (matches the DB `String(80)`), whitespace-
  only crop reaches the service → `ValidationFailed` 422 with the
  AppError shape (belt and braces, documented in tests).
- Request `PUT signals`: `{signals: object, refreshed_at?: ISO}` —
  whole JSON document capped at 50 000 chars (422 on overflow);
  naive `refreshed_at` gets UTC attached (column is `timestamptz`);
  omitted → service uses `now()`.
- No date policy: `planted_on` may be in the future (M019 decision —
  derived `days_since_planted` is exposed as-is, possibly negative).
- Authz is `for_write=True` for PUTs/DELETE, `for_write=False` for the
  GET — identical semantics to M014/M016 (no oracle: cross-tenant →
  404).

#### Frontend Changes
None.

#### External Dependencies
None new.

#### Service Contract Used
As M019: `get_farm_state` (3 queries), `set_plot_state`,
`clear_plot_state`, `put_signals`. The API adds exactly one authz
SELECT before each call (documented; the 3-query contract belongs to
the service layer).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Router module: request models, four routes, service delegation.
3. Register in `src/api/v1/__init__.py`.
4. `tests/api/test_farm_state.py` (fixture pattern copied from
   `test_farms.py`): full matrix ×4 routes, cross-farm/unknown ids,
   stage/crop/signals validation, idempotent PUTs, anon 401.
5. Gate, live verify, docs, state, commits.

#### Acceptance Criteria
- [x] GET returns the full twin view (plots, states, counts, signals)
      for owner farmer and officer; non-owner farmer → 404; anon → 401.
- [x] PUT plot state twice → 204/204 and GET shows the second values;
      bad stage → 422; officer → 403; cross-farm plot → 404.
- [x] DELETE plot state twice → 204/204; state gone from GET.
- [x] PUT signals → 204 and GET reflects the document + refreshed_at;
      oversized document → 422; officer → 403.
- [x] Route-inventory default-deny (M017 test) still green — new
      routes demand auth.
- [x] Full quality gate green.

#### Unit Tests Required
- [x] Request-model validation: stage Literal, crop length, signals size
      cap, naive `refreshed_at` UTC attachment (pure pydantic, no DB).

#### Integration Tests Required
- [x] All matrix paths above against dev Postgres, scoped cleanup (house
  rule).

#### Security Checks Required
- [x] Every route calls `_authorized_farm`/`_authorized_plot` before
      the service (grep-level obvious + behavior tests).
- [x] No service call bypasses authz (officer write → 403, non-owner →
      404 asserted for all four routes).
- [x] Anon → 401 on all four routes; M017 inventory test still green.

#### Performance Checks Required
- [x] GET remains 3 service queries + 1 authz SELECT (no N+1 — one
      LEFT JOIN, asserted by inspection/test where practical).

#### Memory/Resource Checks Required
- [x] Signals document capped at 50 000 chars at the API edge.

#### Failure Scenarios to Handle
- Unknown farm/plot → 404; cross-farm plot id in URL → 404 (plot
  scoped to URL farm by `_authorized_plot`).
- Farm/plot deleted between authz and service call → service
  `NotFound` → 404 (documented race).
- Whitespace-only crop → 422 (`ValidationFailed` AppError shape);
  bad stage → 422 (pydantic shape) — both 422, differing bodies is a
  known inconsistency (see ENGINEERING_STATE debt note).

#### Rollback Strategy
Remove the router module + registration; nothing else depends on it
until M055's frontend.

#### Verification Commands
```bash
uv run pytest tests/api/test_farm_state.py tests/api/test_idor.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No ingestion/provider calls (M022+), no health/risk computation
(M032+), no staleness policy, no caching layer, no new tables.

#### Verification & Notes (added on completion)
- Delivered as spec'd: `src/api/v1/farm_state.py` (tag `farm-state`),
  registered in `src/api/v1/__init__.py`. Growth stage validated by a
  `field_validator` against `GROWTH_STAGES` (not `Literal[...]` —
  mypy can't unpack a `tuple[str, ...]` into Literal and a hard-coded
  Literal would risk schema/DB drift).
- Tests: 14 new (`tests/api/test_farm_state.py`) — two pure request-
  model tests (stage/crop/date validation; size cap, tz attach) +
  twelve HTTP tests covering the full matrix per route (anon 401 /
  officer 403 on writes / non-owner 404 / admin allowed), idempotent
  PUT/DELETE, both 422 shapes (pydantic `detail` vs AppError
  `error_code`), cross-farm plot → 404, unknown ids, wholesale signal
  replace, naive `refreshed_at` → UTC round trip. M017's OpenAPI
  inventory test passed unchanged (default-deny now covers 19 ops).
- Fix found while testing: `age_seconds` right after a PUT is 0
  (sub-second truncation) — assertion adjusted to `>= 0`; pydantic
  serializes UTC as `...Z`, assertions compare parsed datetimes.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **216
  passed** (202 baseline + 14 new); bandit `-r -ll` on `src/api` +
  `src/services` + touched tests = 0; pip-audit clean.
- Live (`uvicorn` on 8000 + `live_m020.py`, 20 checks): full authz
  matrix ×4 routes, happy-path view (days_since_planted = 2462),
  both validation shapes, signals round trip with naive-tz input,
  idempotent delete; cleanup deleted seeded rows. ALL PASS; server
  killed by PID (M009 lesson).

### M021 — Provider interface pattern (abstract base + registry) 🔒

**Priority:** P0 **Depends On:** M002
**Status:** done (lock approved by human 2026-09-28, design as
written)

#### Objective
One consistent, testable pattern for every external-data consumer:
`src/providers/` ships a **base class + errors + registry +
settings-driven mode selection** (`demo`/`live` flags already in
`Settings` since M002), plus **one reference family interface**
(Weather) that proves the pattern end-to-end. M022+ milestones then
only write concrete implementations.

#### Why This Milestone Exists
Six later milestones (M022, M025, M028, M036, M040 + their live
twins) would otherwise each invent their own lookup/selection/error
style. Locking the pattern once — while nothing implements it yet —
is the cheapest moment. 🔒 because this *is* the architecture review.

#### Files Expected to Be Created
- `src/providers/__init__.py` (public exports)
- `src/providers/base.py`
- `src/providers/errors.py`
- `src/providers/registry.py`
- `src/providers/weather.py` (reference family ABC + payload model)
- `tests/providers/__init__.py`
- `tests/providers/test_providers.py`

#### Files Expected to Be Modified
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None. Pure in-process pattern.

#### External Dependencies
None new (pydantic, asyncio only).

#### Architecture (the design under review)

**1. Package `src/providers/`** (peer of `src/ingestion`/`src/services`;
weather/sat/soil feed ingestion, disease/LLM feed `src/ai` — a shared
home avoids duplication).

**2. `errors.py`**
```python
class ProviderError(Exception): ...            # base, safe message
class ProviderNotRegistered(ProviderError)     # family/mode unknown
class ProviderUnavailable(ProviderError)       # upstream down/timeout — retryable
class ProviderResponseInvalid(ProviderError)   # payload violates contract — not retryable
```
Retries/backoff are the **ingestion layer's** job (M023+), never the
provider's.

**3. `base.py`**
```python
class BaseProvider(ABC):
    family: ClassVar[str]  # "weather" | "satellite" | ...
    mode: ClassVar[ProviderMode]  # "demo" | "live"
    name: ClassVar[str]  # e.g. "open-meteo"

    async def aclose(self) -> None:  # no-op; live providers override
        ...
```
Metadata validated by the registry at registration (non-empty,
family in known set, etc.).

**4. `registry.py`**
```python
class ProviderRegistry:                       # instantiable → tests get fresh ones
    def register(cls) -> cls                  # decorator; duplicate (family, mode) → ProviderError
    def get(family, mode) -> BaseProvider     # lazy construct + cache one instance per key
    async def aclose_all() -> None            # shutdown hook for workers
default_registry = ProviderRegistry()
def register(cls) -> cls                      # decorator on default_registry
def get_provider(family, *, mode=None) -> BaseProvider
    # mode defaults to get_settings().<family>_provider ("demo"/"live")
```
Known families are exactly the five settings flags:
`weather, satellite, soil, disease, llm` (family → `f"{family}_provider"`).

**5. `weather.py` — the reference family**
```python
class WeatherReading(BaseModel):      # typed contract, validated at the edge
    fetched_at: datetime
    temperature_c: float | None
    humidity_pct: float | None
    rainfall_mm_24h: float | None
    wind_speed_kmh: float | None
    condition: str | None
    source: str                       # provider name

class WeatherProvider(BaseProvider):
    family = "weather"
    @abstractmethod
    async def fetch(self, lat: float, lon: float) -> WeatherReading: ...

def get_weather_provider(*, mode=None) -> WeatherProvider
    # typed wrapper over get_provider: no casts in call sites
```
M022 implements `WeatherProvider` twice? No — M022 registers the
**demo** implementation under `("weather", "demo")`; M024 registers
`("weather", "live")`. Ingestion M023 calls
`get_weather_provider().fetch(lat, lon)` and folds the reading into
`put_signals`. Families without a `lat/lon` need (disease: image,
LLM: prompt) define their own ABC + typed getter in their milestone,
same shape.

**What deliberately stays out:** concrete providers, HTTP clients,
caching/TTLs, retry policy, DB writes, `signals` document mapping
(all M022+ concerns). No plugin auto-discovery/import magic —
explicit registration only (grep-able, mypy-friendly).

#### Implementation Steps
1. Approval of this design (lock), roadmap → in-progress.
2. `errors.py` → `base.py` → `registry.py` → `weather.py` → exports.
3. Tests (pure unit, no DB/network): register/get, duplicate
   registration rejected, unknown family/mode → ProviderNotRegistered,
   settings-driven default mode (monkeypatched settings), incomplete
   ABC subclass → TypeError, fake weather provider round trip through
   the typed getter, `aclose_all` propagation, registry isolation
   (fresh `ProviderRegistry` per test — never pollute the default one).
4. Gate, docs, state, commits.

#### Acceptance Criteria
- [x] `get_provider("weather")` resolves to the settings-selected mode;
      explicit `mode=` overrides.
- [x] Duplicate `(family, mode)` registration fails fast with a clear
      `ProviderError`.
- [x] Unknown family → `ProviderNotRegistered` naming the family and
      the five known ones.
- [x] `WeatherProvider` cannot be instantiated with `fetch` missing;
      a compliant fake passes through `get_weather_provider()` typed.
- [x] Full quality gate green (pure unit tests, fast).

#### Unit Tests Required
All of the above; zero DB/network (fast suite).

#### Integration Tests Required
None (nothing real to integrate until M022).

#### Security Checks Required
- [x] No secrets/tokens in provider metadata or `repr`; registry does
      not log settings values.

#### Performance Checks Required
- [x] Instances cached per `(family, mode)` — `get_provider` does not
      re-instantiate per call; registration happens at import/startup
      only.

#### Memory/Resource Checks Required
- [x] `aclose_all` releases per-instance resources (tested with a
      fake that records calls).

#### Failure Scenarios to Handle
- Register before settings loaded → fine (mode is read at *get* time,
  not registration time).
- `get_settings()` flags disagree with registered modes (e.g.
  `weather_provider="live"` but only demo registered) →
  `ProviderNotRegistered` listing what *is* registered for the family.
- Misbehaving provider raising `ProviderError` subclasses → pass
  through untouched (ingestion maps them later).

#### Rollback Strategy
Delete `src/providers/` + tests; nothing imports it until M022.

#### Verification Commands
```bash
uv run pytest tests/providers -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No concrete providers (M022/M025/M028/M036/M040), no HTTP/network
calls, no retries, no DB, no caching TTLs, no auto-discovery.

#### Verification & Notes (added on completion)
- Delivered as spec'd: `src/providers/` — `errors.py` (4-class
  hierarchy), `base.py` (`BaseProvider` metadata ClassVars +
  `KNOWN_FAMILIES` + no-op `aclose`), `registry.py`
  (`ProviderRegistry` instantiable / `default_registry` /
  `register` / settings-driven `get_provider`), `weather.py`
  (reference `WeatherProvider` ABC + `WeatherReading` + typed
  `get_weather_provider`), `__init__.py` public exports.
- Design approved by human (lock) before any code — roadmap flipped
  to in-progress only after approval.
- Tests: 15 pure unit tests (`tests/providers/test_providers.py`),
  0.73s, zero DB/network: instance caching, duplicate registration,
  metadata validation (family/mode/name), unknown-family messaging
  (lists known families + what's registered per family), settings
  default vs explicit mode (monkeypatched `default_registry` +
  `get_settings` — never pollutes the process registry, house rule),
  incomplete-ABC → TypeError, typed round trip, wrong-implementation
  rejection, `aclose_all` close + re-construct, error hierarchy, repr.
- Fixes during lint/mypy: `aclose` body `return None` (ruff B027),
  `pytest.raises(ValidationError)` instead of blind `Exception`
  (B017), `ClassVar[Any]` annotations on intentionally-bad test
  classes (mypy misc), `model_validate` for missing-required-field
  checks (mypy call-arg), message assertion matched the actual
  `mode='live'` header rather than an invented `weather/live` slug.
- **Tooling note (found by the gate): ruff 0.16.9 formats Markdown
  code blocks** — `scripts/check.ps1` runs `ruff format --check .`
  over `MILESTONES.md` too; aligned trailing comments in the spec's
  fenced blocks failed the gate until `uv run ruff format .`.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **231
  passed** (216 baseline + 15 new); bandit `-r -ll` on
  `src/providers` + `tests/providers` = 0; pip-audit clean.
- Live (`live_m021.py`, in-process): settings flags ×5, register →
  settings-driven `get_provider` → typed getter → validated reading,
  instance caching, `ProviderNotRegistered` shape, `aclose_all`
  re-construct, registry isolation, unload — 10/10 ALL PASS.

### M022 — Weather demo provider

**Priority:** P0 **Depends On:** M021
**Status:** done

#### Objective
`src/providers/weather_demo.py`: the first concrete provider — a
**deterministic, network-free** synthetic weather source registered on
the default registry under `("weather", "demo")`, so
`get_weather_provider()` works with default settings and M023's
ingestion has something real to consume.

#### Why This Milestone Exists
Proves the M021 pattern end-to-end with a consumer-visible artifact,
and gives the whole demo/CI story a stable backend: same coordinates
always produce the same reading (assertable in tests, predictable in
the demo).

#### Files Expected to Be Created
- `src/providers/weather_demo.py`
- `tests/providers/test_weather_demo.py`

#### Files Expected to Be Modified
- `src/providers/__init__.py` (explicit registration import)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None.

#### External Dependencies
None (stdlib `hashlib` only — deliberately: the demo provider must
work with no network, no keys, no extra packages).

#### Decisions
- **Determinism:** values derive from
  `sha256(f"{lat:.4f},{lon:.4f}")` → one integer seed per point
  (4-decimal precision ≈ 11 m — stable against float jitter).
- **Documented ranges** (checked by tests): `temperature_c`
  18.0–32.9, `humidity_pct` 40–90, `rainfall_mm_24h` 0.0–11.9,
  `wind_speed_kmh` 1–45, `condition` from
  `("clear", "partly_cloudy", "cloudy", "light_rain", "thunderstorm")`.
- `fetched_at` = now (UTC); `source` = `name` = `"demo-weather-v1"`.
- **Coordinate guard:** lat ∉ [-90,90] or lon ∉ [-180,180] →
  `ValueError` (caller bug, not an upstream failure — not a
  `ProviderError`).
- **Registration:** explicit import line in
  `src/providers/__init__.py` with a comment (grep-able list; no
  entry-point/auto-discovery magic — honoring M021's stated rule).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `weather_demo.py`: seed helper + `DemoWeatherProvider`.
3. Registration import in `src/providers/__init__.py`.
4. Tests (pure unit).
5. Gate, live, docs, state, commits.

#### Acceptance Criteria
- [x] `get_weather_provider()` under default settings returns the demo
      provider (registration works through the normal path).
- [x] Same coordinates → identical field values; two different
      coordinates → at least one differing field.
- [x] All five fields within documented ranges; `WeatherReading`
      validates; `source == "demo-weather-v1"`.
- [x] Out-of-range coordinates → `ValueError`.
- [x] Full quality gate green.

#### Unit Tests Required
All of the above (pure, fast, no DB/network).

#### Integration Tests Required
- [x] Registry path test: `get_provider("weather")` (settings default
  `demo`) resolves to the registered class via `default_registry`.

#### Security Checks Required
- [x] No network calls, no keys, no PII at rest; coordinates are used
      only as hash input (not logged).

#### Performance Checks Required
- [x] One sha256 per fetch (negligible); instance comes from the
      registry cache (no per-call construction).

#### Memory/Resource Checks Required
- [x] No resources to release; `aclose` stays the base no-op.

#### Failure Scenarios to Handle
- Invalid coordinates → `ValueError` with a safe message.
- Demo provider cannot fail otherwise (no I/O) — upstream failure
  classes stay unexercised until M024's live provider.

#### Rollback Strategy
Delete `weather_demo.py` + its import line + tests; M021 pattern
untouched.

#### Verification Commands
```bash
uv run pytest tests/providers -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No HTTP/Open-Meteo (M024), no `signals` document mapping or DB writes
(M023 owns ingestion), no realism requirements beyond the documented
ranges (demo is allowed to look synthetic).

#### Verification & Notes (added on completion)
- Delivered as spec'd: `src/providers/weather_demo.py`
  (`DemoWeatherProvider`, sha256 seed at 4-decimal coordinate
  precision, documented ranges, WGS84 guard) + explicit registration
  import in `src/providers/__init__.py` (comment-marked list, no
  auto-discovery — M021 rule honored).
- Tests: 14 new (`tests/providers/test_weather_demo.py`) —
  settings-path registration (real `default_registry`; M021's
  isolation tests unaffected since they use monkeypatched/local
  registries), determinism (excl. `fetched_at`), distinct points
  differ, 5-point range grid, `fetched_at` recency, coordinate guard
  ×4, seed stability incl. 4-decimal jitter absorption. Also proved
  `register`-as-decorator works with mypy.
- mypy fix: `WeatherReading` fields are `float | None` by contract —
  range test extracts locals with `is not None` guards first.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **245
  passed** (231 baseline + 14 new); bandit `-r -ll` on
  `src/providers` + `tests/providers` = 0; pip-audit clean.
- Live (`live_m022.py`, in-process): settings flag demo →
  settings-path resolution → Nairobi reading (temp 24.0 C, humidity
  70%, rain 9.5 mm, wind 43 km/h, light_rain) → determinism →
  Mombasa differs (24.2 C, thunderstorm) → out-of-range ValueError —
  6/6 ALL PASS. (Script fix during live: `dataclasses.asdict` doesn't
  work on pydantic models — `model_dump()`.)

### M023 — Weather ingestion service + storage table

**Priority:** P0 **Depends On:** M022, M019
**Status:** done

#### Objective
First full provider→storage pipeline: a `weather_observations` history
table (rev 0007), a `WeatherObservation` model, and
`src/ingestion/weather.py` that turns a `WeatherReading` into
(a) an observation row and (b) the `weather` key of the farm's signal
cache — merging with any other family keys already there. A thin
worker (`workers/weather_ingest.py`) runs it over the dev farms.

#### Why This Milestone Exists
Proves the whole vertical: M021 pattern → M022 demo provider → M019
cache write path, with per-provider merging happening exactly where
M019 said it would (the ingestion layer). M031's normalization and
the engines all consume what this milestone persists.

#### Files Expected to Be Created
- `alembic/versions/0007_weather_observations.py` (hand-written)
- `src/models/weather_observation.py`
- `src/ingestion/weather.py`
- `workers/weather_ingest.py`
- `tests/ingestion/__init__.py`
- `tests/ingestion/test_weather_ingestion.py`

#### Files Expected to Be Modified
- `src/models/__init__.py`
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes (rev 0007, hand-written — never trust autogenerate)
```sql
CREATE TABLE weather_observations (
    id              uuid PRIMARY KEY,            -- app-side uuid4 (M008 pattern)
    farm_id         uuid NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    provider        varchar(40) NOT NULL,        -- e.g. demo-weather-v1
    observed_at     timestamptz NOT NULL,        -- reading.fetched_at
    temperature_c   double precision NULL,
    humidity_pct    double precision NULL,
    rainfall_mm_24h double precision NULL,
    wind_speed_kmh  double precision NULL,
    condition       varchar(40) NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_weather_observations_farm_observed
    ON weather_observations (farm_id, observed_at DESC);
```
History grain: **append-only** — every successful ingest adds a row
(re-runs are not deduplicated; the cache always holds the latest).
No `updated_at` (rows are immutable).

#### API Changes / Frontend Changes
None (worker entry point, no HTTP).

#### External Dependencies
None (uses M022 demo provider through `get_weather_provider()`).

#### Service Contract
```python
# src/ingestion/weather.py
def weather_signals_doc(reading: WeatherReading) -> dict
    # {"weather": {temperature_c, humidity_pct, rainfall_mm_24h,
    #   wind_speed_kmh, condition, observed_at (iso), source}}
    # RAW provider units — M031 owns normalization.

async def ingest_weather_for_farm(session, farm_id, *, provider=None) -> IngestResult
    # 1) farm centroid (ST_Centroid) — NULL geo → status "skipped_no_geo"
    # 2) provider.fetch(lat, lon) (default: get_weather_provider())
    #    ProviderUnavailable/ProviderResponseInvalid → "provider_error"
    #    (logged, counted, no partial writes — fetch happens BEFORE any insert)
    # 3) insert observation row + commit
    # 4) merge: read existing signals → signals["weather"] = doc → put_signals
    #    (other family keys preserved; put_signals commits — M019 pattern)
    # raises NotFound for unknown farm_id

async def ingest_weather_for_all(session, *, provider=None) -> IngestSummary
    # iterates every farm; per-farm failures isolated (rollback + count);
    # returns IngestSummary(ingested, skipped_no_geo, provider_error, failed)

# DTOs: IngestResult(farm_id, status, observation_id?, detail?)
#       IngestSummary(... counts ..., results: list[IngestResult])
# status ∈ {"ingested", "skipped_no_geo", "provider_error", "failed"}
```
Failure/atomicity note (documented): step 3 commits before step 4, so
a crash between them leaves an observation row with a stale cache —
the next run heals the cache; no data loss, only a briefly stale
snapshot (acceptable at demo scale, logged if it ever happens).

#### Worker
```bash
uv run python -m workers.weather_ingest              # all farms
uv run python -m workers.weather_ingest --farm <uuid> # one farm
```
Prints one line per farm + summary; exit 0 even with per-farm errors
(summary shows them), non-zero only on catastrophic failure (DB down).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Hand-written rev 0007 + `WeatherObservation` model + export.
3. `src/ingestion/weather.py` service + DTOs.
4. `workers/weather_ingest.py` (arg parse, stats, print).
5. Tests (dev Postgres, scoped cleanup).
6. Gate, live, docs, state, commits.

#### Acceptance Criteria
- [x] Ingest on a geo farm → observation row + `signals.weather`
      populated; pre-existing `signals.satellite` key survives merge.
- [x] Farm with NULL geo → `skipped_no_geo`, no provider call, no row.
- [x] Failing provider (fake) → `provider_error`, zero rows written.
- [x] Second ingest → second observation row (append-only history).
- [x] Unknown farm → `NotFound`.
- [x] Worker end-to-end on dev DB (live check).
- [x] Full quality gate green.

#### Unit Tests Required
- [x] `weather_signals_doc` mapping (iso `observed_at`, all fields, raw
  units).

#### Integration Tests Required
All acceptance paths above against dev Postgres; seeded rows cleaned
by scoped user delete (FK cascade reaches farms → observations +
signal caches).

#### Security Checks Required
- [x] No authz surface (no HTTP); worker is a trusted local process.
- [x] No secrets in logs — status lines carry farm id + status only.

#### Performance Checks Required
- [x] Per farm: 1 provider call + ≤5 small queries (centroid, insert,
      cache read, cache upsert); farms iterate sequentially (dozens at
      demo scale — concurrency deliberately out of scope).

#### Memory/Resource Checks Required
- [x] One session for the whole worker run, closed at the end;
      engine disposed on exit.

#### Failure Scenarios to Handle
- NULL farm geometry → skip (documented), not an error.
- Provider raises `ProviderError` subclass → counted, next farm still
  processed (per-farm try/except + rollback).
- Cache read-modify-write race with a concurrent API write →
  last-writer-wins on the whole doc (put_signals semantics; demo has
  no concurrent writers — documented).

#### Rollback Strategy
`alembic downgrade 0006` drops the table; delete service/worker/
tests; M019/M021/M022 untouched.

#### Verification Commands
```bash
uv run pytest tests/ingestion tests/test_migrations.py -v
uv run python -m workers.weather_ingest --farm <uuid>
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live HTTP provider (M024), no unit/timeframe normalization
(M031), no scheduler/cron, no ingestion API endpoints, no satellite
/soil families (M025–M030), no per-observation dedup.

#### Verification & Notes (added on completion)
- Delivered as spec'd: rev 0007 `weather_observations` (hand-written),
  `WeatherObservation` model + export, `src/ingestion/weather.py`
  (`weather_signals_doc` / `ingest_weather_for_farm` /
  `ingest_weather_for_all` + `IngestResult`/`IngestSummary`),
  `workers/weather_ingest.py` (`--farm` optional). `alembic check` =
  "No new upgrade operations detected" (model ≡ migration).
- **Deviation (logged):** index created **ASC** `(farm_id,
  observed_at)` instead of the spec's `DESC` — Postgres scans it
  backward for `ORDER BY observed_at DESC`, and the ASC form keeps
  model metadata byte-comparable for `alembic check` (string column
  names in `__table_args__` can't carry a reliable `.desc()`).
- **Fixture lesson (reproduced + fixed):** any DB-touching test must
  request `_db` even when it doesn't need seeded users —
  `test_unknown_farm_raises_not_found` initially omitted it, leaving
  an undisposed pool connection bound to its torn-down event loop;
  the *next* test's reachability probe then failed with a misleading
  "dev Postgres not reachable" skip. Bisected via `-k` pairs before
  the fix.
- Tests: 10 new (`tests/ingestion/test_weather_ingestion.py`) —
  signals-doc mapping, merge preserving `satellite` key +
  `refreshed_at == reading.fetched_at`, default-settings provider path
  (proves M022 wiring), append-only history (2 rows / 1 cache),
  no-geo skip without provider call (provider would explode),
  provider-failure = zero writes, `NotFound`, batch counts across 3
  farms, batch isolation (`RuntimeError` → `failed` + rollback,
  batch continues), worker `_run(farm)` exit code + printed status.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **255
  passed** (245 baseline + 10 new); bandit `-r -ll` on
  `src/ingestion` + `workers` + `src/models` + `tests/ingestion` = 0;
  pip-audit clean.
- Live: seeded 2 farms (geo/no-geo) → `python -m workers.weather_ingest`
  twice (both runs: `ingested=1 skipped_no_geo=1 provider_error=0
  failed=0`; verify → **2 observation rows** = append-only, cache
  weather doc with all raw fields + `observed_at` ISO) → `--farm`
  single mode `ingested` → cleanup left `observations remaining=0`.
  ALL PASS.

---

### M025 — Satellite/NDVI demo provider

**Priority:** P0 **Depends On:** M021
**Status:** done

#### Objective
First satellite-family pair: `src/providers/satellite.py` (the family
contract — `SatelliteReading`, abstract `SatelliteProvider.fetch`,
typed `get_satellite_provider`) plus `src/providers/satellite_demo.py`
— a **deterministic, network-free** synthetic NDVI source registered on
the default registry under `("satellite", "demo")`, so
`get_satellite_provider()` works with default settings and M026's
ingestion has something real to consume.

#### Why This Milestone Exists
M021 shipped only the weather family; satellite is the second family
and proves the pattern generalizes (family ABC + typed getter +
explicit registration line, zero weather-specific hooks). NDVI is the
core agronomic signal behind crop-health overlays (M047+), and the
demo story needs a stable, assertable backend for M026's pipeline.

#### Files Expected to Be Created
- `src/providers/satellite.py`
- `src/providers/satellite_demo.py`
- `tests/providers/test_satellite.py`

#### Files Expected to Be Modified
- `src/providers/__init__.py` (contract exports + explicit registration import)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None.

#### External Dependencies
None (stdlib `hashlib` only — same network-free demo rule as M022).

#### Decisions
- **Contract shape mirrors weather:** required `fetched_at` (UTC) +
  `source`; optional payload `ndvi: float | None` (vegetation index)
  and `cloud_cover_pct: float | None` (quality gate input for
  M026/M031).
- **`captured_at: datetime | None`** — a satellite scene is captured
  at overpass time and fetched later; the demo sets it equal to
  `fetched_at` ("just overflown"). M026 will store it as the scene
  time. Weather needed no such field (fetch time == observation time).
- **No pydantic range constraints on the payload** (consistent with
  `WeatherReading`): documented demo ranges are test-enforced here;
  validation/quality policy belongs to M031.
- **Determinism:** same `sha256(f"{lat:.4f},{lon:.4f}")` seed scheme
  as M022 — duplicated locally (2nd occurrence of the helper; extract
  to a shared module only if M028's soil demo lands identical logic —
  rule of three).
- **Documented ranges** (checked by tests): `ndvi` 0.10–0.90 (2
  decimals), `cloud_cover_pct` 0–100 (step 1).
- `fetched_at` = `captured_at` = now (UTC); `source` = `name` =
  `"demo-satellite-v1"`.
- **Coordinate guard:** lat ∉ [-90,90] or lon ∉ [-180,180] →
  `ValueError` (caller bug — not a `ProviderError`), same message
  shape as weather's.
- **Registration:** one comment-marked import line in
  `src/providers/__init__.py` (M021's no-auto-discovery rule).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `satellite.py` contract (`SatelliteReading`, `SatelliteProvider`,
   `get_satellite_provider`).
3. `satellite_demo.py` (`DemoSatelliteProvider` + local seed helper).
4. Exports + registration line in `src/providers/__init__.py`.
5. Tests (pure unit).
6. Gate, live check, docs, state, commits.

#### Acceptance Criteria
- [x] `get_satellite_provider()` under default settings returns the
      demo provider through the normal registry path.
- [x] Same coordinates → identical payload (`ndvi`,
      `cloud_cover_pct`); two different coordinates → differing
      payload.
- [x] `ndvi` within 0.10–0.90, `cloud_cover_pct` within 0–100;
      `SatelliteReading` validates; `source == "demo-satellite-v1"`;
      `captured_at == fetched_at` (demo semantics), both UTC.
- [x] Out-of-range coordinates → `ValueError`.
- [x] Full quality gate green.

#### Unit Tests Required
All of the above (pure, fast, no DB/network).

#### Integration Tests Required
- [x] Registry path test: `get_provider("satellite")` (settings default
  `demo`) resolves via the real `default_registry`.

#### Security Checks Required
- [x] No network, no keys, no PII; coordinates used only as hash input
      (not logged).

#### Performance Checks Required
- [x] One sha256 per fetch; provider instance served from the registry
      cache (no per-call construction).

#### Memory/Resource Checks Required
- [x] No resources to release; `aclose` stays the base no-op.

#### Failure Scenarios to Handle
- Invalid coordinates → `ValueError` with a safe message.
- Demo provider cannot fail otherwise (no I/O); upstream failure
  classes stay unexercised until M027's live provider.

#### Rollback Strategy
Delete `satellite.py` + `satellite_demo.py` + their import/export
lines + tests; M021 pattern and the weather family untouched.

#### Verification Commands
```bash
uv run pytest tests/providers -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live satellite/NDVI API (M027), no `signals` document mapping or
DB writes (M026 owns satellite ingestion), no NDVI time series /
compositing / cloud masking / quality gating (M031+), no plot-level
overlays (M047+).

#### Verification & Notes (added on completion)
- Delivered as spec'd: `src/providers/satellite.py`
  (`SatelliteReading` with `ndvi`/`cloud_cover_pct`/`captured_at`,
  abstract `SatelliteProvider.fetch`, typed `get_satellite_provider`
  with isinstance guard) + `src/providers/satellite_demo.py`
  (`DemoSatelliteProvider`, sha256 seed at 4-decimal precision,
  documented ranges ndvi 0.10–0.90 / cloud 0–100, WGS84 guard,
  `captured_at == fetched_at`) + exports/registration in
  `src/providers/__init__.py`.
- **Second family proves the pattern generalizes:** zero changes needed
  to base/errors/registry/config (`satellite_provider` flag and
  `KNOWN_FAMILIES` entry already existed from M009/M021) — only the
  contract module, demo module, and one import/export block.
- isort nuance: strict module sorting places `satellite_demo`'s
  registration import *between* the two family contract imports
  (`satellite` < `satellite_demo` < `weather`); the registration-list
  comment was reworded to describe the grep-able `registers on import`
  pattern instead of implying a contiguous block.
- Tests: 14 new (`tests/providers/test_satellite.py`) — settings-path
  registration (real `default_registry`), determinism (excl. both time
  fields), distinct points differ, 5-point range grid incl. 2-decimal
  ndvi + integer cloud assertions, demo time semantics
  (`captured_at == fetched_at`, recent UTC), coordinate guard ×4,
  seed stability incl. 4-decimal jitter absorption. 43 total in
  `tests/providers`.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **269
  passed** (255 baseline + 14 new); bandit `-r -ll` on `src/providers`
  + `tests/providers` = 0; pip-audit clean.
- Live (`live_m025.py`, in-process): **10/10 ALL PASS** — settings
  flag demo → registry resolution + typed accessor instance caching →
  Nairobi reading (ndvi 0.46, cloud 49) → determinism → Mombasa
  differs (ndvi 0.72, cloud 81) → source/time semantics →
  out-of-range `ValueError`.
---

### M026 — Satellite ingestion service + storage table

**Priority:** P0 **Depends On:** M025, M019
**Status:** done

#### Objective
Satellite vertical mirrors the weather one: rev `0008` creates the
append-only `satellite_observations` history table;
`src/ingestion/satellite.py` turns a `SatelliteReading` into (a) an
observation row and (b) a `signals.satellite` cache merge that
**preserves every other family key** (notably `weather`, M023);
`workers/satellite_ingest.py` runs it for all farms or one.

#### Why This Milestone Exists
The farm-state cache (M019) reserves a `satellite` slot that only an
ingestion service can populate, and NDVI history is what crop-health
views (M047+) and M031's quality gating read. It also proves the
ingestion pattern is family-agnostic: same statuses, same failure
policy, different payload.

#### Files Expected to Be Created
- `src/models/satellite_observation.py`
- `alembic/versions/0008_satellite_observations.py` (hand-written)
- `src/ingestion/satellite.py`
- `workers/satellite_ingest.py`
- `tests/ingestion/test_satellite_ingestion.py`

#### Files Expected to Be Modified
- `src/models/__init__.py` (export `SatelliteObservation`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
`alembic` revision **0008** (down_revision `0007`), one table:

```
satellite_observations
  id            uuid PK (client-side uuid4)
  farm_id       uuid NOT NULL FK → farms.id ON DELETE CASCADE
  provider      varchar(40) NOT NULL
  observed_at   timestamptz NOT NULL  -- SCENE CAPTURE time
                (= reading.captured_at, fallback reading.fetched_at)
  ndvi          float NULL
  cloud_cover_pct float NULL
  created_at    timestamptz NOT NULL, server_default now()
  INDEX (farm_id, observed_at) ASC   -- same convention as 0007
```

- Append-only: no `updated_at`, no updates through the service.
- **No `raw_units` JSONB** (deviation from the weather table, by
  design): NDVI is unitless and cloud is explicitly pct — the full
  payload already lives in columns; M031 has nothing unit-wise to
  recover here.
- `tests/test_migrations.py`'s derived-head assertion auto-covers the
  new revision (no pin to update).

#### API Changes / Frontend Changes
None (API for observations is not yet a milestone; overlays M047+).

#### External Dependencies
None (stdlib `hashlib` demo provider only).

#### Decisions
- **Ingestion logic mirrors `src/ingestion/weather.py` line-for-line**
  in structure: fetch-before-write (`ProviderError` → zero writes),
  observation commit then cache merge (two-step, crash healed next
  run), centroid via `ST_X/ST_Y(ST_Centroid(Farm.geo))`, per-farm
  try/except + rollback isolation in the batch, `NotFound` for unknown
  farms, `skipped_no_geo` without calling the provider.
- **`observed_at` = `captured_at or fetched_at`** — the scene time is
  the observation time for satellite; fallback keeps live providers
  (M027) that omit `captured_at` working.
- **`signals.satellite` doc:** `{ndvi, cloud_cover_pct, observed_at
  (ISO), source}`; `refreshed_at` = `reading.fetched_at` (fetch time,
  per M019's column semantics).
- **Result dataclasses duplicated** from the weather module
  (`IngestResult`/`IngestSummary`, same shapes): keeps this milestone
  purely additive (rollback = delete files, zero M023 regression
  surface). Rule of three — extract to a shared `src/ingestion`
  helper when M029 (soil) makes the third copy.
- **Worker CLI mirrors `workers/weather_ingest.py`:** `--farm`
  optional, one status line per farm + summary, exit 0 even with
  per-farm failures.
- Index direction/`alembic check` parity lesson from M023 carries
  over (ASC index, hand-written migration, `alembic check` must say
  "No new upgrade operations detected").

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Model + export; hand-written migration 0008.
3. `src/ingestion/satellite.py` (signals doc, result types, per-farm
   + batch ingest).
4. `workers/satellite_ingest.py`.
5. Tests (mirror `tests/ingestion/test_weather_ingestion.py`).
6. `alembic check`, gate, live check, docs, state, commits.

#### Acceptance Criteria
- [x] Ingest on a geo farm → observation row + `signals.satellite`
      populated; pre-existing `signals.weather` key survives merge.
- [x] Farm with NULL geo → `skipped_no_geo`, no provider call, no row.
- [x] Failing provider (fake) → `provider_error`, zero rows written.
- [x] Second ingest → second observation row (append-only history);
      `observed_at` equals the scene time (demo: `captured_at`).
- [x] Unknown farm → `NotFound`.
- [x] Worker end-to-end on dev DB (live check), incl. `--farm` mode.
- [x] `alembic check` clean; full quality gate green.

#### Unit Tests Required
- [x] `satellite_signals_doc` mapping (ISO `observed_at` from
      `captured_at`, source, both payload fields).

#### Integration Tests Required
All acceptance paths above against dev Postgres; seeded rows cleaned
by scoped user delete (FK cascade reaches farms → satellite
observations + signal caches).

#### Security Checks Required
- [x] No authz surface (no HTTP); worker is a trusted local process.
- [x] No secrets in logs — status lines carry farm id + status only.

#### Performance Checks Required
- [x] Per farm: 1 provider call + ≤5 small queries (same shape as
      M023); sequential batch (dozens at demo scale).

#### Memory/Resource Checks Required
- [x] One session for the whole worker run, closed at the end;
      engine disposed on exit.

#### Failure Scenarios to Handle
- Invalid farm id → `NotFound`; no geometry → skip; provider raises
  `ProviderError` → status without writes; anything else →
  `failed` + rollback, batch continues.
- Fixture house rule (M023 lesson): every DB-touching test requests
  `_db`, even without seeded users.

#### Rollback Strategy
`alembic downgrade 0007`, delete the new files + export line; cache
merges written under `signals.satellite` remain valid JSON (keys are
family-namespaced).

#### Verification Commands
```bash
uv run pytest tests/ingestion tests/test_migrations.py -v
uv run alembic check
uv run python -m workers.satellite_ingest --farm <uuid>
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live satellite API (M027), no quality gating/cloud masking/
compositing/NDVI time series (M031+), no scheduler/cron, no ingestion
API endpoints, no plot-level overlays (M047+), no soil family (M029).

#### Verification & Notes (added on completion)
- Delivered as spec'd: rev 0008 `satellite_observations`
  (hand-written, `alembic check` = "No new upgrade operations
  detected"), `SatelliteObservation` + export, `src/ingestion/satellite.py`
  (`satellite_signals_doc` / `ingest_satellite_for_farm` /
  `ingest_satellite_for_all`, logger `agrin.ingestion.satellite`),
  `workers/satellite_ingest.py` (`--farm` optional).
- **Cross-family merge proved both directions:** M023's test proved
  `satellite` survives a weather merge; this milestone's test +
  live check prove `weather` survives a satellite merge (pre-seeded
  `{"weather": {"temperature_c": 21.5}}` intact after ingest).
- `observed_at` = `captured_at or fetched_at` (scene time) — stored on
  the row AND in the signals doc; `refreshed_at` = `fetched_at` (M019
  column semantics). Two unit tests pin the preference and the
  `captured_at=None` fallback.
- **Deliberate deviation from the weather table:** no `raw_units`
  JSONB (NDVI unitless, cloud explicit pct — payload fully covered by
  columns; nothing for M031 to recover). `IngestResult`/`IngestSummary`
  duplicated from the weather module to keep this milestone purely
  additive — rule of three: extract to a shared `src/ingestion` helper
  when M029 (soil) makes the third copy.
- M023 fixture house rule applied from the start: every DB-touching
  test requests `_db` (incl. `test_unknown_farm_raises_not_found`).
- Tests: 11 new (`tests/ingestion/test_satellite_ingestion.py`) —
  signals-doc mapping + captured-at fallback, merge preserving
  `weather` key + `refreshed_at == fetched_at`, default-settings
  provider path (proves M025 wiring), append-only history (2 rows/1
  cache), no-geo skip without provider call, provider-failure zero
  writes, `NotFound`, batch counts across 3 farms, batch isolation
  (`RuntimeError` → `failed` + rollback, batch continues), worker
  `_run(farm)` exit code + printed status. 280 total.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **280
  passed** (269 baseline + 11 new); bandit `-r -ll` on `src/ingestion`
  + `src/models` + `workers` + `tests/ingestion` = 0; pip-audit clean.
- Live (live_m026.py + real worker): seeded 2 farms (geo/no-geo,
  weather key pre-seeded) → `python -m workers.satellite_ingest` ×2
  (both: `ingested=1 skipped_no_geo=1 provider_error=0 failed=0`;
  verify after run 2 = **7/7**: 2 observation rows = append-only,
  ndvi 0.82 in range, weather key survived, satellite cache doc
  complete, no_geo clean) → `--farm` single mode `ingested` →
  cleanup left `satellite observations remaining=0`. ALL PASS.
---

### M028 — Soil demo provider

**Priority:** P0 **Depends On:** M021
**Status:** done

#### Objective
Third family pair, same shape as M025: `src/providers/soil.py`
(`SoilReading`, abstract `SoilProvider.fetch`, typed
`get_soil_provider`) + `src/providers/soil_demo.py` — a
deterministic, network-free synthetic soil source registered under
`("soil", "demo")` so `get_soil_provider()` resolves with default
settings and M029's ingestion has something real to consume.

**Rule-of-three refactor rides along:** this milestone's demo provider
is the *third* copy of the coordinate seed helper and the WGS84 guard
(M022 weather, M025 satellite) — both extract into a shared
`src/providers/_demo.py` (`point_seed`, `check_wgs84`), and the two
existing demo providers are switched over (import-only change; their
behavior and tests stay green).

#### Why This Milestone Exists
Completes the demo trio (weather/satellite/soil) the farm-state cache
was designed for (M019's `signals` slots), and forces the pattern
through its third instance — the point where copy-paste drift would
start, so the shared helpers land *before* M029/M030.

#### Files Expected to Be Created
- `src/providers/soil.py`
- `src/providers/soil_demo.py`
- `src/providers/_demo.py`
- `tests/providers/test_soil.py`

#### Files Expected to Be Modified
- `src/providers/weather_demo.py`, `src/providers/satellite_demo.py`
  (use shared `_demo` helpers — internal refactor, public behavior
  unchanged)
- `tests/providers/test_weather_demo.py`,
  `tests/providers/test_satellite.py` (seed-helper import only)
- `src/providers/__init__.py` (contract exports + registration import)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None.

#### External Dependencies
None (stdlib `hashlib` only — network-free demo rule).

#### Decisions
- **Contract mirrors weather/satellite:** required `fetched_at` (UTC)
  + `source`; optional payload — `soil_moisture_pct` (plant-available
  water, %), `ph`, `soil_temperature_c`, `nitrogen_kg_ha` (available
  N). Soil is in-situ: no `captured_at` (fetch time == observation
  time, like weather).
- **No pydantic range constraints** (consistent with the other two
  families); documented demo ranges are test-enforced; quality policy
  = M031.
- **Documented ranges** (checked by tests): `soil_moisture_pct`
  20.0–60.0, `ph` 5.5–7.5, `soil_temperature_c` 12.0–28.0 (all 1
  decimal), `nitrogen_kg_ha` 20–120 (integer).
- **Determinism:** sha256 of `f"{lat:.4f},{lon:.4f}"` via the new
  shared `point_seed()`; WGS84 guard via `check_wgs84()` (raises the
  same `ValueError` message as before — caller bug, not
  `ProviderError`).
- `fetched_at` = now (UTC); `source` = `name` = `"demo-soil-v1"`.
- **Registration:** one comment-marked import line in
  `src/providers/__init__.py` (M021 no-auto-discovery rule).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Shared `_demo.py` (`point_seed`, `check_wgs84`); switch
   `weather_demo.py` + `satellite_demo.py` to it; update the two
   existing tests' import only.
3. `soil.py` contract; `soil_demo.py` implementation.
4. Exports + registration line in `src/providers/__init__.py`.
5. Tests (`test_soil.py`; existing suites must stay green).
6. Gate, live check, docs, state, commits.

#### Acceptance Criteria
- [x] `get_soil_provider()` under default settings returns the demo
      provider through the normal registry path.
- [x] Same coordinates → identical payload; two different coordinates
      → differing payload.
- [x] All four fields within documented ranges; `SoilReading`
      validates; `source == "demo-soil-v1"`; `fetched_at` recent UTC.
- [x] Out-of-range coordinates → `ValueError` (via shared
      `check_wgs84`).
- [x] Weather + satellite demo suites still pass after the helper
      extraction (same values, same guard message).
- [x] Full quality gate green.

#### Unit Tests Required
All of the above (pure, fast, no DB/network).

#### Integration Tests Required
- [x] Registry path test: `get_provider("soil")` (settings default
  `demo`) resolves via the real `default_registry`.

#### Security Checks Required
- [x] No network, no keys, no PII; coordinates used only as hash input
      (not logged).

#### Performance Checks Required
- [x] One sha256 per fetch; provider instance served from the registry
      cache.

#### Memory/Resource Checks Required
- [x] No resources to release; `aclose` stays the base no-op.

#### Failure Scenarios to Handle
- Invalid coordinates → `ValueError` with the shared safe message.
- Demo provider cannot fail otherwise (no I/O); upstream failure
  classes stay unexercised until M030's live provider.

#### Rollback Strategy
`git revert` the milestone commit (pure refactor + additive files; no
DB/API surface). Shared `_demo.py` removal is safe only when all
three demo providers revert together.

#### Verification Commands
```bash
uv run pytest tests/providers -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live soil API (M030), no `signals` document mapping or DB writes
(M029 owns soil ingestion), no moisture/EC/NPK measurement science or
quality gating (M031+), no per-plot soil differences (soil is
per-farm, M019 grain decision).

#### Verification & Notes (added on completion)
- Delivered as spec'd: `src/providers/soil.py` (`SoilReading` —
  `soil_moisture_pct`/`ph`/`soil_temperature_c`/`nitrogen_kg_ha`
  optional, no `captured_at` since soil is in-situ; abstract
  `SoilProvider.fetch`; typed `get_soil_provider`) +
  `src/providers/soil_demo.py` (`DemoSoilProvider`, `demo-soil-v1`,
  documented ranges 20.0–60.0 / 5.5–7.5 / 12.0–28.0 (1 dp) and
  20–120 integer N) + exports/registration line.
- **Rule-of-three extraction landed:** new shared
  `src/providers/_demo.py` (`point_seed`, `check_wgs84` — identical
  sha256 scheme and ValueError message); `weather_demo.py` +
  `satellite_demo.py` switched over (hashlib/`_seed`/inline-guard
  removed from both); their tests now import `point_seed as _seed`
  (import-only change). Behavior proven unchanged: full suites green
  (weather 14 + satellite 14) and the live cross-check reproduced the
  exact M022/M025 values for Nairobi (temp 24.0 C, ndvi 0.46).
- isort interleaving (demo import right after its family contract)
  produced a correct sorted block with the three registration lines —
  comment reworded to describe the grep-able `registers on import`
  pattern rather than a contiguous block.
- Tests: 15 new (`tests/providers/test_soil.py`) — settings-path
  registration, determinism, distinct points, 5-point range grid with
  1-dp/integer assertions, fetched_at recency, coordinate guard ×4,
  shared `point_seed` stability incl. jitter absorption, plus a
  three-family extraction guard test. **58 total** in
  `tests/providers`.
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **295
  passed** (280 baseline + 15 new); bandit `-r -ll` on `src/providers`
  + `tests/providers` = 0; pip-audit clean.
- Live (`live_m028.py`, in-process): **14/14 ALL PASS** — settings
  flag demo → registry + typed accessor caching → Nairobi reading
  (moisture 28.5, ph 6.4, temp 16.1, N 48) → determinism → Mombasa
  differs (moisture 23.2, ph 5.5) → shared-guard ValueError →
  weather + satellite demos still fetch post-extraction with their
  original M022/M025 values.
- **Ordering note:** executed P0-first (human-confirmed 2026-09-28):
  M024/M027 (live providers, P1) intentionally deferred until the
  P0 trio (M025/M026/M028 + M029) is complete.
---

### M029 — Soil ingestion service + storage table

**Priority:** P0 **Depends On:** M028, M019
**Status:** done

#### Objective
Soil vertical completes the demo trio: rev `0009` creates the
append-only `soil_observations` history table;
`src/ingestion/soil.py` turns a `SoilReading` into (a) an observation
row and (b) a `signals.soil` cache merge that **preserves every other
family key** (`weather`, `satellite`); `workers/soil_ingest.py` runs
it for all farms or one.

**Rule-of-three refactor rides along:** `IngestResult` / `IngestSummary`
/ `IngestStatus` are about to be copied a third time (defined
verbatim in `src/ingestion/weather.py` since M023 and
`src/ingestion/satellite.py` since M026) — they extract into
`src/ingestion/_shared.py`, and the two existing services import from
there (no external importers exist; internal behavior unchanged).

#### Why This Milestone Exists
Closes the third `signals` slot the farm-state cache was designed
with (M019), and finishes the P0 demo slice: after this milestone
every family has provider → ingestion → storage working offline, so
the P1 live providers (M024/M027) and M030 land against a proven
pipeline.

#### Files Expected to Be Created
- `src/models/soil_observation.py`
- `alembic/versions/0009_soil_observations.py` (hand-written)
- `src/ingestion/soil.py`
- `src/ingestion/_shared.py`
- `workers/soil_ingest.py`
- `tests/ingestion/test_soil_ingestion.py`

#### Files Expected to Be Modified
- `src/ingestion/weather.py`, `src/ingestion/satellite.py` (import
  the shared result types — definitions removed, call sites unchanged)
- `src/models/__init__.py` (export `SoilObservation`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
`alembic` revision **0009** (down_revision `0008`), one table:

```
soil_observations
  id            uuid PK (client-side uuid4)
  farm_id       uuid NOT NULL FK → farms.id ON DELETE CASCADE
  provider      varchar(40) NOT NULL
  observed_at   timestamptz NOT NULL  -- in-situ: = reading.fetched_at
  soil_moisture_pct float NULL
  ph            float NULL
  soil_temperature_c float NULL
  nitrogen_kg_ha float NULL
  created_at    timestamptz NOT NULL, server_default now()
  INDEX (farm_id, observed_at) ASC   -- same convention as 0007/0008
```

- Append-only: no `updated_at`, no updates through the service.
- **No `raw_units` JSONB** (same rationale as 0008): units are encoded
  in the column names (`_pct`, `_c`, `_kg_ha`); nothing to recover.
- No `captured_at` column: soil is in-situ (fetch time == observation
  time; unlike satellite's 0008).
- `tests/test_migrations.py`'s derived-head assertion auto-covers the
  new revision.

#### API Changes / Frontend Changes
None.

#### External Dependencies
None.

#### Decisions
- **Structure mirrors `src/ingestion/weather.py` /
  `src/ingestion/satellite.py` line-for-line:** fetch-before-write,
  observation commit then cache merge (two-step), centroid via
  `ST_X/ST_Y(ST_Centroid(Farm.geo))`, per-farm try/except + rollback
  isolation, `NotFound` / `skipped_no_geo` statuses, sequential batch,
  logger `agrin.ingestion.soil`.
- **`observed_at` = `reading.fetched_at`** (no `captured_at` on
  `SoilReading`).
- **`signals.soil` doc:** `{soil_moisture_pct, ph,
  soil_temperature_c, nitrogen_kg_ha, observed_at (ISO), source}`;
  `refreshed_at` = `reading.fetched_at`.
- **Shared extraction:** `src/ingestion/_shared.py` owns
  `IngestStatus` / `IngestResult` / `IngestSummary` (moved verbatim);
  weather + satellite switch their imports (grep proved zero external
  importers — tests reference only the `ingest_*` functions and
  `*_signals_doc`). Soil imports them directly from `_shared`.
- **Worker CLI mirrors the other two:** `--farm` optional, status
  lines + summary, exit 0 with per-farm failures.
- ASC index + hand-written migration + `alembic check` parity (M023
  lesson carried through).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `_shared.py` extraction; weather + satellite import switch.
3. Model + export; hand-written migration 0009.
4. `src/ingestion/soil.py`.
5. `workers/soil_ingest.py`.
6. Tests (`test_soil_ingestion.py`, mirror of the other two suites).
7. `alembic check`, gate, live check, docs, state, commits.

#### Acceptance Criteria
- [x] Ingest on a geo farm → observation row + `signals.soil`
      populated; pre-existing `weather` + `satellite` keys survive.
- [x] Farm with NULL geo → `skipped_no_geo`, no provider call, no row.
- [x] Failing provider (fake) → `provider_error`, zero rows written.
- [x] Second ingest → second observation row; `observed_at` equals
      `fetched_at` (in-situ time).
- [x] Unknown farm → `NotFound`.
- [x] Weather + satellite ingestion suites still green after the
      `_shared` extraction.
- [x] Worker end-to-end on dev DB (live check), incl. `--farm` mode.
- [x] `alembic check` clean; full quality gate green.

#### Unit Tests Required
- [x] `soil_signals_doc` mapping (ISO `observed_at`, all four payload
      fields, source).

#### Integration Tests Required
All acceptance paths above against dev Postgres; seeded rows cleaned
by scoped user delete (FK cascade).

#### Security Checks Required
- [x] No authz surface (no HTTP); worker is a trusted local process.
- [x] No secrets in logs — status lines carry farm id + status only.

#### Performance Checks Required
- [x] Per farm: 1 provider call + ≤5 small queries; sequential batch.

#### Memory/Resource Checks Required
- [x] One session for the whole worker run, closed at the end;
      engine disposed on exit.

#### Failure Scenarios to Handle
- Unknown farm → `NotFound`; no geometry → skip; `ProviderError` →
  status without writes; anything else → `failed` + rollback, batch
  continues. `_db` fixture on every DB-touching test (house rule).

#### Rollback Strategy
`alembic downgrade 0008`, delete the new files + export line; the
`_shared.py` extraction reverts independently (weather/satellite keep
working either way — same class shapes).

#### Verification Commands
```bash
uv run pytest tests/ingestion tests/test_migrations.py -v
uv run alembic check
uv run python -m workers.soil_ingest --farm <uuid>
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live soil API (M030), no quality gating/measurement science
(M031+), no scheduler/cron, no ingestion API endpoints, no plot-level
soil variation (per-farm grain, M019).

#### Verification & Notes (added on completion)
- Delivered as spec'd: rev 0009 `soil_observations` (hand-written,
  `alembic check` = "No new upgrade operations detected"),
  `SoilObservation` + export, `src/ingestion/soil.py`
  (`soil_signals_doc` / `ingest_soil_for_farm` / `ingest_soil_for_all`,
  logger `agrin.ingestion.soil`), `workers/soil_ingest.py`
  (`--farm` optional), `src/ingestion/_shared.py`.
- **Rule-of-three extraction landed:** `IngestStatus`/`IngestResult`/
  `IngestSummary` moved verbatim into `src/ingestion/_shared.py`;
  weather + satellite switched to the shared import (grep proved zero
  external importers — call sites and test references unchanged).
  Guard test (`test_shared_result_types_used_by_all_families`)
  asserts identity of the classes across all three modules; weather +
  ingestion suites stayed green (32/32 in `tests/ingestion`).
- **All three family slots now coexist:** live check pre-seeded
  `weather` + `satellite` keys and proved both survive the soil merge
  (cache = `{weather, satellite, soil}`), the final M019 design state.
- `observed_at` = `fetched_at` (in-situ; no `captured_at` anywhere in
  soil's schema or contract).
- Tests: 11 new (`tests/ingestion/test_soil_ingestion.py`) — shared
  extraction guard, signals-doc mapping, merge preserving weather +
  satellite keys + `refreshed_at == fetched_at`, default-settings
  provider path (proves M028 wiring), append-only history, no-geo
  skip without provider call, provider-failure zero writes,
  `NotFound`, batch counts, batch isolation, worker `_run` print.
  **306 total.**
- Gate: `scripts/check.ps1` PASSED — ruff format/check, mypy, **306
  passed** (295 baseline + 11 new); bandit `-r -ll` on `src/ingestion`
  + `src/models` + `workers` + `tests/ingestion` = 0; pip-audit clean.
- Live (live_m029.py + real worker): seeded 2 farms (geo/no-geo,
  weather+satellite keys pre-seeded) → `python -m workers.soil_ingest`
  ×2 (both: `ingested=1 skipped_no_geo=1 provider_error=0 failed=0`;
  verify after run 2 = **8/8**: 2 append-only rows, moisture 28.5 /
  ph 6.2 in range, weather + satellite keys survived, soil cache doc
  complete, no_geo clean) → `--farm` mode `ingested` → cleanup left
  `soil observations remaining=0`. ALL PASS.
- **P0 demo trio complete (M025/M026/M028/M029).** Next per
  human-confirmed ordering: P1s M024 (weather live) / M027 (satellite
  live), then P2 M030 (soil live).

---

### M024 — Weather live provider (Open-Meteo)

**Priority:** P1 **Depends On:** M023
**Status:** done

#### Objective
`src/providers/weather_live.py`: the first network-backed provider —
`LiveWeatherProvider` registered under `("weather", "live")` calling
Open-Meteo's free forecast API (no API key), mapping the response to
`WeatherReading`. `get_weather_provider(mode="live")` works;
default settings stay `demo`.

#### Why This Milestone Exists
First exercise of the M021 failure taxonomy in anger
(`ProviderUnavailable` / `ProviderResponseInvalid` mapping from real
network faults), and the switch that turns the platform from
pure-demo into live-capable. Every later live provider (M027, M030,
M040) follows the shape established here.

#### Files Expected to Be Created
- `src/providers/weather_live.py`
- `tests/providers/test_weather_live.py`

#### Files Expected to Be Modified
- `src/providers/__init__.py` (export + explicit registration import)
- `pyproject.toml`, `uv.lock` (httpx promoted dev → runtime; pin
  unchanged at `0.28.1`, human-approved)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None.

#### External Dependencies
- **httpx==0.28.1 promoted to runtime** (was dev-only; same pin —
  human-confirmed 2026-09-28, D8).
- Open-Meteo forecast API (free tier, no key):
  `GET https://api.open-meteo.com/v1/forecast` with
  `latitude, longitude, current=temperature_2m,relative_humidity_2m,
  precipitation,weather_code,wind_speed_10m, timezone=auto`.
  Network reachable from this host (verified before spec'ing).

#### Decisions
- **Construction:** `LiveWeatherProvider(client=None, base_url=...)`
  — owns an `httpx.AsyncClient` (10 s timeout, module constant);
  injectable client/base_url for tests (MockTransport) and the live
  unreachable-host check. Registry caches one instance per process;
  `aclose()` overridden to close the client (base no-op replaced).
- **Field mapping:** `temperature_2m` → `temperature_c`,
  `relative_humidity_2m` → `humidity_pct`, `wind_speed_10m` →
  `wind_speed_kmh`, `precipitation` (current hour, mm) →
  `rainfall_mm_24h` — **documented approximation**: the contract has
  only a 24h slot; Open-Meteo `current` exposes hourly precipitation.
  Stored raw in the signals doc; M031 owns semantics.
  `weather_code` (WMO) → `condition` via a documented table:
  0 → clear; 1–2 → partly_cloudy; 3/45/48 → cloudy; 51–67, 80–82 →
  light_rain; **71–77, 85–86 (snow) → cloudy** (vocabulary has no
  snow value); 95–99 → thunderstorm; unknown codes → cloudy.
- `fetched_at` = now (UTC); `source` = `name` = `"open-meteo-v1"`.
- **Error mapping:** `httpx.TimeoutException`/`TransportError` →
  `ProviderUnavailable`; HTTP 5xx or 429 → `ProviderUnavailable`;
  other non-2xx (4xx) → `ProviderResponseInvalid`; unparseable body
  or missing `current` object → `ProviderResponseInvalid`. Missing
  individual `current` fields → `None` payload (contract is all
  optional). Raw exceptions never escape (M021 contract).
- **No WGS84 guard:** live coordinates come from PostGIS centroids
  (always valid) and Open-Meteo validates requests itself; a 400 maps
  to `ProviderResponseInvalid`.
- **Tests never hit the network:** `httpx.MockTransport` only; the
  real call happens in the live check.
- **Registration:** one comment-marked import line in
  `src/providers/__init__.py` (M021 rule); settings default stays
  `demo` so nothing else changes behavior.

#### Implementation Steps
1. Spec (here), roadmap → in-progress; pyproject httpx promotion +
   `uv sync --extra dev` (host lesson: bare `uv sync` prunes the dev
   *extra*).
2. `weather_live.py` (client ownership, mapping tables, error taxon
   mapping).
3. Exports + registration line.
4. Tests (`MockTransport`-based, offline).
5. Gate, live check (real HTTP), docs, state, commits.

#### Acceptance Criteria
- [x] `get_weather_provider(mode="live")` returns the live provider;
      default settings still resolve demo.
- [x] Canned Open-Meteo JSON maps to the expected `WeatherReading`
      (all five fields + condition table incl. snow→cloudy and
      unknown→cloudy).
- [x] Timeouts/connect errors/5xx/429 → `ProviderUnavailable`; 4xx/
      bad JSON/missing `current` → `ProviderResponseInvalid`; no raw
      exception escapes.
- [x] Missing optional `current` fields → `None` payload fields.
- [x] `aclose()` closes the owned client.
- [x] Real-network live check: Nairobi + Mombasa readings plausible;
      deliberate 400 maps to `ProviderResponseInvalid`; refused
      connection maps to `ProviderUnavailable`.
- [x] Full quality gate green (offline).

#### Unit Tests Required
All mapping/error paths above via `httpx.MockTransport` (pure, no
network).

#### Integration Tests Required
- [x] Registry path: `get_provider("weather", mode="live")` resolves
  the registered class via the real `default_registry`.

#### Security Checks Required
- [x] No API keys (Open-Meteo keyless); no secrets logged — error
  messages carry httpx/HTTP status text only; coordinates sent to a
  documented public endpoint (farm centroids, not PII).
- [x] bandit + pip-audit clean after the dep promotion.

#### Performance Checks Required
- [x] One pooled `AsyncClient` per process (registry-cached
  provider), 10 s timeout bounds every call, sequential ingest batch
  unchanged.

#### Memory/Resource Checks Required
- [x] `aclose()` releases the client; worker/registry never leaks a
  client across processes.

#### Failure Scenarios to Handle
- DNS/connect refused/timeout → `ProviderUnavailable` (ingestion
  records `provider_error`, batch continues — M023 machinery).
- Rate limit (429) → `ProviderUnavailable`.
- 4xx (bad request) → `ProviderResponseInvalid`.
- Malformed/partial JSON → `ProviderResponseInvalid` or `None`
  fields as specified above.

#### Rollback Strategy
Delete `weather_live.py` + its import/export lines + tests;
`pyproject.toml`/`uv.lock` revert independently (dev-only pin was
functionally sufficient for the demo path).

#### Verification Commands
```bash
uv run pytest tests/providers -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No scheduler/cron (M034+), no retry/backoff policy beyond the single
call's timeout (ingestion layer owns skip decisions), no API-key
management (Open-Meteo is keyless), no unit normalization (M031), no
provider health dashboards.

#### Verification & Notes (added on completion)
- Gate PASSED (2026-09-29, live dev DB on 65432): `ruff format --check`
  OK, `ruff check` OK, `mypy` OK (102 source files), `pytest` **363
  passed / 0 skipped** (306 prior + 57 new in
  `tests/providers/test_weather_live.py`); `bandit -r -ll
  src/providers workers` = 0 findings; `pip-audit` = no known
  vulnerabilities.
- **Live check `live_m024.py` (real HTTP, 4/4 PASS):** Nairobi
  `22.4C / 48% / 0.0mm / 15.1km/h / partly_cloudy`, Mombasa
  `26.1C / 81% / 0.0mm / 16.9km/h / clear` (both `source=
  open-meteo-v1`, plausible ranges); `latitude=999` → upstream
  **400** → `ProviderResponseInvalid`; `http://127.0.0.1:9` (closed
  port) → `ProviderUnavailable` ("All connection attempts failed").
  Deliberate-400 used the real upstream rather than a stub, so the
  status mapping was proven against Open-Meteo's own error body.
- **Decision refinement (logged):** the spec table said "unknown codes
  → cloudy" without distinguishing *absent* codes; an absent/null
  `weather_code` now yields `condition=None` (no data), while a
  present-but-unreadable value (string/bool) or an unknown numeric
  code still folds to `cloudy`. Rationale: the acceptance criterion
  requires missing optional `current` fields → `None`, and the
  5-value vocabulary must not invent an observation upstream never
  reported. `WeatherObservation.condition` and the signals doc are
  nullable, so no schema change was needed.
- **Finding:** `httpx.MockTransport` propagates handler exceptions
  unchanged, so the taxonomy tests exercise the real client code path
  (no monkeypatching of `AsyncClient`); timeouts, connect errors and
  status mapping are all covered end-to-end through `fetch`.
- **Finding:** the registry-resolution test builds a real
  `AsyncClient` (no request is made), so it releases it with
  `default_registry.aclose_all()` in a `finally` — the shared
  registry must never keep an open client lying around between test
  modules.
- **Finding:** `uv sync` alone prunes the dev extra on this host; the
  post-`pyproject.toml` resync must be `uv sync --extra dev`.
- Roadmap row + spec status flipped to `done` only after the gate and
  the live check both passed (status discipline: `done` = committed).

---

### M027 — Satellite live provider (NASA MODIS NDVI)

**Priority:** P1 **Depends On:** M026
**Status:** done

#### Objective
`src/providers/satellite_live.py`: `LiveSatelliteProvider` registered
under `("satellite", "live")`, fetching **real NDVI for a WGS84 point**
from the ORNL DAAC MODIS/VIIRS subset REST web service
(`MOD13Q1` — Terra 16-day, 250 m vegetation index) and mapping it to
`SatelliteReading` (`ndvi`, `cloud_cover_pct`, `captured_at`).
`get_satellite_provider(mode="live")` works; default settings stay
`demo`.

#### Why This Milestone Exists
Second live provider — proves M024's shape (client ownership +
failure taxonomy + MockTransport tests + live check) generalizes to a
non-trivial upstream that needs a **two-request protocol** (composite
calendar → subset). It is also the last P1 whose dependencies are met
(M030 is P2; M038/M051/M052/M053 are P1 but blocked on P0 specs that
do not exist yet).

#### Files Expected to Be Created
- `src/providers/satellite_live.py`
- `tests/providers/test_satellite_live.py`

#### Files Expected to Be Modified
- `src/providers/__init__.py` (export + explicit registration import)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None.

#### External Dependencies
- **httpx==0.28.1** (runtime since M024/D8). No new package pins.
- **ORNL DAAC TESViS REST web service** (free, **no API key, no
  account**): `https://modis.ornl.gov/rst/api/v1/MOD13Q1/{dates,subset}`.
  Reachability and response shape verified from this host before
  spec'ing (Nairobi/Mombasa/London/Sydney all returned NDVI).

#### Decisions
- **Source selection (why MODIS, not Sentinel):** every Sentinel-2 /
  Copernicus / Google Earth Engine path needs credentials we cannot
  mint autonomously (`Settings` has no key fields, M002), and the
  keyless STAC routes (Earth Search, Planetary Computer) would require
  decoding Cloud Optimised GeoTIFFs — a new heavy runtime dep
  (rasterio) and a real raster pipeline. The ORNL DAAC service is
  keyless, JSON, point-based and covers the globe. **Trade-off logged:
  250 m / 16-day instead of 10 m / 5-day** — M031 owns timeframe
  normalization; `signals.satellite` already stores raw values.
- **Two-request protocol:** (1) `GET /MOD13Q1/dates?latitude&longitude`
  returns the composite calendar (entries `{modis_date, calendar_date}`;
  it is the *global* MODIS calendar — same list for every point, so it
  cannot by itself prove data exists); (2) `GET /MOD13Q1/subset` with
  `startDate = endDate =` the newest `calendar_date <= today`, which
  returns that one composite. Rationale: a single look-back window
  costs O(composites) upstream (**11 s for 3 composites**, measured)
  while one date costs ~3 s, and a fixed window can silently miss the
  newest composite when NASA's latency grows (measured latency at
  Nairobi: 47 days).
- **Subset window:** `kmAboveBelow=1&kmLeftRight=1` → `ncols=nrows=9`
  (231.66 m cell → ~2 km across). Small enough to be "the farm's
  pixel", big enough for a meaningful cloud fraction.
- **NDVI:** mean of the QA-valid pixels of that window —
  `pixel_reliability ∈ {0 (good), 1 (marginal)}` and value in
  `[-2000, 10000]` — × `0.0001` (MOD13Q1 scale factor), rounded to
  4 dp. Snow/ice (2), cloudy (3), failed (4) and fill (-1) pixels are
  excluded because **the product's own QA says they are not data**;
  this is QA handling, not a cloud-masking *policy* (M031 owns
  policy). No usable pixel → `ndvi=None`.
- **`cloud_cover_pct` approximation:** `100 × count(pixel_reliability
  == 3) / 81`, rounded to 1 dp. MOD13Q1 ships no cloud-cover band, so
  the QA "cloudy" flag is the honest source; stored raw for M031 —
  same documented-approximation pattern as M024's precipitation slot.
- **`captured_at`** = the composite's `calendar_date` at 00:00 UTC
  (overpass/composite day), distinct from `fetched_at` = now (UTC) —
  M025's semantics.
- `source` = `name` = `"ornl-daac-modis-mod13q1"`.
- **Error mapping:** timeout/transport/5xx/429 →
  `ProviderUnavailable`; every other non-2xx (including the upstream's
  plain-text `400 No data available for time period …`) →
  `ProviderResponseInvalid`; HTTP 200 with `subset` empty or missing
  the NDVI/quality bands, non-list payloads or wrong value types →
  `ProviderResponseInvalid`. Raw exceptions never escape (M021).
- **Empty `subset` is `ProviderResponseInvalid`, not a null reading**
  (ocean / outside coverage): a successful upstream answer that
  carries no usable payload must not be written as a real observation;
  M023 records `provider_error` and the batch continues.
- **Client ownership:** identical to M024 — owns one pooled
  `httpx.AsyncClient` (`TIMEOUT_S = 20.0`; measured `dates` ≈ 2.5–4.5 s,
  single-date `subset` ≈ 3 s), injectable `client`/`base_url` for
  MockTransport tests and the live refused-connection check;
  `aclose()` closes it.
- **Registration:** one comment-marked import line in
  `src/providers/__init__.py`; settings default stays `demo`.
- **Tests never hit the network:** `httpx.MockTransport` dispatching on
  the request path (`/dates` vs `/subset`); real HTTP only in the live
  check.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `satellite_live.py` (two-request protocol, QA filtering, taxonomy).
3. Exports + registration line.
4. Tests (`MockTransport`, offline).
5. Gate, live check (real HTTP), docs, state, commits.

#### Acceptance Criteria
- [x] `get_satellite_provider(mode="live")` resolves the live provider
      through the real `default_registry`; default settings still
      resolve demo.
- [x] Canned `/dates` + `/subset` payloads map to the expected
      `SatelliteReading`: QA-valid NDVI mean × 0.0001 (4 dp),
      cloud % from the QA flag (1 dp), `captured_at` from
      `calendar_date`, `fetched_at` recent/UTC, correct `source`.
- [x] QA filtering proven: fill/cloud/snow/failed pixels excluded from
      the mean; cloudy pixels counted into `cloud_cover_pct`; no
      usable pixel → `ndvi=None`.
- [x] Timeout/connect errors/5xx/429 → `ProviderUnavailable`; 4xx/
      empty `subset`/missing bands/bad types →
      `ProviderResponseInvalid`; no raw exception escapes.
- [x] `aclose()` closes the owned client.
- [x] Real-network live check: Nairobi + Mombasa + one cloudy point
      give plausible NDVI/cloud values; deliberate 400 maps to
      `ProviderResponseInvalid`; refused connection maps to
      `ProviderUnavailable`.
- [x] Full quality gate green (offline).

#### Unit Tests Required
All mapping/QA/taxonomy paths via `httpx.MockTransport` (pure, no
network).

#### Integration Tests Required
- [x] Registry path: `get_provider("satellite", mode="live")` resolves
  the registered class via the real `default_registry`.

#### Security Checks Required
- [x] No API keys or credentials anywhere (keyless upstream); no
  secrets in URLs or log lines; only farm centroids are sent, to a
  documented NASA/ORNL endpoint.
- [x] bandit + pip-audit clean (no new dependencies).

#### Performance Checks Required
- [x] Two HTTP calls per fetch (~5–6 s measured end to end), one
  pooled client per process, 20 s timeout bounds each call.

#### Memory/Resource Checks Required
- [x] `aclose()` releases the client; the registry cache never leaks a
  client across processes.

#### Failure Scenarios to Handle
- DNS/connect refused/timeout → `ProviderUnavailable`.
- Upstream 5xx/429 → `ProviderUnavailable`.
- Upstream 400 (`No data available for time period`, bad params) →
  `ProviderResponseInvalid`.
- Empty `subset` (no coverage) → `ProviderResponseInvalid`.
- Missing NDVI/quality band, non-list `data`, empty `dates`, an
  unparseable `calendar_date`, or no composite dated ≤ today →
  `ProviderResponseInvalid`.
- All pixels QA-invalid → reading with `ndvi=None` (still a valid
  reading; the cloud figure explains why).

#### Rollback Strategy
Delete `satellite_live.py` + its import/export lines + tests; nothing
else references the live mode (settings default remains `demo`, so no
behavior changes on rollback).

#### Verification Commands
```bash
uv run pytest tests/providers -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No time-series/compositing across scenes (latest composite only), no
invented cloud-masking policy beyond the product's QA, no HTTP-layer
caching/retry/backoff (single attempt per call; ingestion owns skip
decisions), no DB writes (M026), no unit/timeframe normalization
(M031), no API-key settings (upstream is keyless).

#### Verification & Notes (added on completion)
- Gate PASSED (2026-09-29, live dev DB on 65432): `ruff format --check`
  OK, `ruff check` OK, `mypy` OK (104 source files), `pytest` **403
  passed / 0 skipped** (363 prior + 40 new in
  `tests/providers/test_satellite_live.py`); `bandit -r -ll
  src/providers workers` = 0 findings; `pip-audit` = no known
  vulnerabilities (no dependency added for this milestone).
- **Live check `live_m027.py` (real HTTP, 8/8 PASS):** Nairobi
  `ndvi=0.2731 / 0.0% cloud`, Mombasa `0.3508 / 0.0%`, Amazon
  rainforest `0.8581` (asserted ≥ 0.5), Oman desert `0.109`
  (asserted ≤ 0.3), Sydney `0.3947 / 66.7% cloud` — all
  `captured_at=2026-08-13`, `source=ornl-daac-modis-mod13q1`;
  ocean point `(0, -140)` → `ProviderResponseInvalid`; real upstream
  **404** → `ProviderResponseInvalid` with the trimmed upstream text;
  closed port `127.0.0.1:9` → `ProviderUnavailable`.
- **Deviation (logged):** the spec's "deliberate 400" became a
  deliberate **404**. The provider only ever requests a date the
  upstream calendar just handed it, so there is no request shape we
  can drive at ORNL that reliably yields a 400; a bogus base path
  yields a genuine upstream 4xx through the *same* code branch
  (`status != 200 → ProviderResponseInvalid`), which is what the
  criterion is really about. The upstream's own 400 wording
  (`No data available for time period …`) is unit-covered with a
  mocked response.
- **Finding:** `/dates` returns the **global** MODIS calendar — the
  identical 610-entry list for a mid-ocean point — so it proves
  nothing about coverage; only `/subset` does. Recorded so nobody
  later "optimizes" it into a coverage check.
- **Finding:** upstream cost is O(composites returned): 3 composites
  = 11.5 s vs 1 composite ≈ 3 s, and NASA's latency at Nairobi
  measured **47 days** (2026-08-13 composite observed on
  2026-09-29). Together these are why the two-request protocol beat a
  look-back window: a window is both slower and latently fragile.
- **Finding:** the upstream answers 4xx/`404` with **plain text**, not
  JSON. It is surfaced trimmed to `UPSTREAM_MESSAGE_MAX = 200`
  chars (`"modis HTTP 404 on dates: \"Product bogus not found.\""`) —
  actionable, and still not a raw payload dump.
- **Finding:** tests derive every date from `datetime.now(UTC).date()`
  at import time (`PAST_DAY`/`LATEST_DAY`/`FUTURE_DAY`), so the
  "newest composite ≤ today" selection can never rot as the calendar
  advances — copy this pattern for any future date-sensitive provider
  test.
- isort: `satellite_live`'s registration import sorts directly after
  `satellite_demo` and before `soil`, keeping the one-line-per-provider
  block greppable.

### M031 — Data normalization layer (units/timeframes → Farm State)

**Priority:** P0 **Depends On:** M023, M026, M029
**Status:** done

#### Objective
A read-side, DB-free normalization layer that turns the raw
`farm_signal_caches.signals` document (three provider families, raw
provider units, raw timestamps) into canonical pydantic models the
analysis engines consume: canonical units, documented timeframe
conversions, physical-range plausibility, the canonical condition
vocabulary, and per-family `age_seconds` — provenance-preserving, with
staleness *thresholds* deliberately left to M032+.

#### Why This Milestone Exists
M023/M026/M029 all store "payload fields as fetched" and M025/M029
both delegated quality policy to M031. Without this layer every engine
(M032 crop health, M033 risk, M034 recommendations) would re-implement
per-source unit/timeframe handling, and swapping demo → live providers
would leak source quirks straight into decision logic.

#### Files Expected to Be Created
- `src/services/normalize.py`
- `tests/services/test_normalize.py`

#### Files Expected to Be Modified
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None. Pure read-side transformation of data already persisted by M019's
cache; no migration, no endpoint, no ingestion change.

#### External Dependencies
None (stdlib + pydantic).

#### Service Contract
```python
# src/services/normalize.py
CANONICAL_CONDITIONS: tuple[str, ...] = (
    "clear", "partly_cloudy", "cloudy", "light_rain", "thunderstorm")

SOURCE_PROFILES: dict[str, SourceProfile]   # source -> timeframe facts
    # demo-weather-v1           -> rainfall window 24 h
    # open-meteo-v1             -> rainfall window 1 h
    # demo-satellite-v1         -> ndvi support 1 day (single overpass)
    # ornl-daac-modis-mod13q1   -> ndvi support 16 days (composite)
    # demo-soil-v1              -> ndvi n/a, rainfall n/a (in-situ)

def normalize_signals(
    signals: Mapping[str, Any], *,
    now: datetime | None = None,            # default datetime.now(UTC)
    refreshed_at: datetime | None = None,   # the cache row's refreshed_at
) -> NormalizedSignals

def normalize_farm_state(
    state: FarmStateView, *, now: datetime | None = None,
) -> NormalizedFarmState                    # NormalizedFarmState(view, signals)

class NormalizedWeather(BaseModel):
    source: str | None
    observed_at: datetime | None            # tz-aware UTC
    age_seconds: int | None                 # now - observed_at (may be negative)
    temperature_c: float | None             # deg C, -90..60
    humidity_pct: float | None              # 0..100
    rainfall_mm: float | None               # amount over rainfall_window_hours
    rainfall_window_hours: int | None       # 24 | 1 | None (unknown source)
    rainfall_mm_per_day: float | None       # amount * 24 / window; None if unknown
    wind_speed_kmh: float | None            # >= 0
    condition: str | None                   # canonical vocabulary, else None

class NormalizedSatellite(BaseModel):
    source: str | None
    observed_at: datetime | None
    age_seconds: int | None
    ndvi: float | None                      # unitless, -1..1
    ndvi_support_days: int | None           # temporal support of the value
    cloud_cover_pct: float | None           # 0..100

class NormalizedSoil(BaseModel):
    source: str | None
    observed_at: datetime | None
    age_seconds: int | None
    soil_moisture_pct: float | None         # 0..100
    ph: float | None                        # 0..14
    soil_temperature_c: float | None        # -90..60
    nitrogen_kg_ha: float | None            # >= 0

class NormalizedSignals(BaseModel):
    weather: NormalizedWeather | None       # None when the family key is absent
    satellite: NormalizedSatellite | None
    soil: NormalizedSoil | None
    refreshed_at: datetime | None
    refreshed_age_seconds: int | None
    unknown_families: list[str]             # non-family keys, sorted
    malformed_families: list[str]           # family keys whose value isn't a mapping

class NormalizedFarmState(BaseModel):
    view: FarmStateView                     # plots/crops as M019 built them
    signals: NormalizedSignals
```

#### Decisions
- **Read-time, not write-time.** The cache stays raw exactly as M019
  contracted ("per-provider merging is the ingestion layer's job";
  "RAW provider units — M031 owns normalization"). No double-write, no
  migration, no ingestion edit; normalization is a pure function of
  (signals doc, refreshed_at, now).
- **Profile-based timeframe conversion, never guessing.** `SOURCE_PROFILES`
  maps a known `source` label to its timeframe facts (rainfall window,
  NDVI temporal support). An unknown or absent source yields `None` for
  every profile-derived field — converting without knowing the window
  would be inventing data. This is the "timeframes" half of the
  milestone title.
- **Plausibility bounds are *physical*, not agronomic** (the quality
  policy M025/M029 handed to this milestone): out-of-range → `None`,
  because an impossible value is not data. Crop thresholds
  (e.g. "NDVI < 0.4 is stress") are decision logic and stay in M032+.
- **No coercion of strings/bools** — `True` or `"22.4"` in the doc is
  not a number the layer will trust; JSONB numbers only. `bool` is
  explicitly excluded before the `int/float` test.
- **No staleness policy.** `age_seconds` / `refreshed_age_seconds` are
  computed; *thresholds* stay with the engines (M019's standing rule).
  Future `observed_at` yields a negative age rather than an error.
- **Condition vocabulary is the platform's 5 values** (both providers
  already fold into them); anything else normalizes to `None`.
- **Malformed ≠ unknown:** a family key holding a non-mapping is
  reported in `malformed_families` and read as absent; non-family keys
  land in `unknown_families`. Both sorted, so tests are stable.
- **Timestamps:** ISO-8601 strings as ingestion wrote them; tz-naive is
  assumed UTC (documented), unparseable/non-str → `None`.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `normalize.py`: constants, `SourceProfile`, the three payload models,
   `normalize_signals` (coerce → bounds → vocabulary → profile → ages).
3. `normalize_farm_state` bundle over `FarmStateView`.
4. Tests (pure unit, no DB — no `_db` fixture needed).
5. Gate, docs, state, two commits (implementation + hash record).

#### Testing Criteria
`tests/services/test_normalize.py` (pure unit, DB-free):
- [x] empty doc → every family `None`, both lists empty.
- [x] full demo doc → round-trips canonical values; ages computed from `now`.
- [x] rainfall windows: demo → window 24 + `mm_per_day == mm`; open-meteo →
  window 1 + `mm_per_day == mm * 24`; unknown source → window and
  `mm_per_day` both `None`.
- [x] NDVI support: demo 1 d, MODIS 16 d, unknown source `None`.
- [x] out-of-bounds → `None` for each bounded field (humidity 150, pH 15,
  NDVI 1.5, temp 999, cloud −5, soil moisture 120, N −3, wind −1).
- [x] `NaN`/`inf`, `True`, `"22.4"`, `null` → `None`.
- [x] unknown condition → `None`; canonical conditions pass through.
- [x] timestamps: aware → UTC, naive → assumed UTC, garbage/non-str →
  `None`, missing → `age_seconds None`, future → negative age.
- [x] family key holding a list → `malformed_families` + family `None`;
  extra key → `unknown_families` (sorted).
- [x] `normalize_farm_state(view)` bundles view + signals (incl. `None`
  cache → all families `None`).

#### Verification Commands
```bash
uv run pytest tests/services/test_normalize.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No staleness thresholds or freshness policy (M032+), no crop/soil
decision thresholds (M032/M033/M034), no DB access (callers pass the
doc or the `FarmStateView`), no ingestion/cache rewrites, no schema
change, no API endpoint, no ingestion of a fourth family.

#### Verification & Notes (added on completion)
- Gate PASSED (2026-09-29, live dev DB on 65432): `ruff format --check`
  OK (109 files), `ruff check` OK, `mypy` OK (106 source files),
  `pytest` **467 passed / 0 skipped** (403 prior + 64 new in
  `tests/services/test_normalize.py`); `bandit -r -ll src workers` = 0
  findings; `pip-audit` = no known vulnerabilities (no dependency
  added).
- **No live check by design:** the layer is a pure function of data
  already persisted — there is no network or DB code path to exercise.
- **Finding:** the two weather sources really do disagree on the
  rainfall window — demo is a 24 h accumulation, Open-Meteo's slot is
  *current hour* — so `rainfall_mm_24h` in the cache is not
  self-describing. The profile converts (hour × 24) and labels the
  window instead of pretending the field name is the truth.
- **Finding:** NASA's NDVI is a 16-day composite while the demo's is a
  single overpass; engines comparing two farms would silently compare
  different temporal supports. `ndvi_support_days` makes the support
  explicit so M032/M033 can discount it rather than discover it.
- **Finding:** `NaN`/`inf` can reach the document (Postgres `jsonb`
  stores them, and Python arithmetic can produce them) and `True` /
  `"22.4"` arrive if anyone hand-edits the cache — all three are
  rejected before the range test (`_number`), which is why the bool
  check precedes the `int | float` test and `math.isfinite` runs
  before the bounds.
- Deviation (harmless): the contract's family builders are written as
  three private helpers (`_weather_family` / `_satellite_family` /
  `_soil_family`) plus a shared `_base` (source, observed_at, age);
  the spec showed the results, not the internals. No public surface
  differs from the contract above.

### M032 — Crop health analysis engine (rule-based)

**Priority:** P0 **Depends On:** M031
**Status:** done

#### Objective
A pure, deterministic rule engine that turns a `NormalizedFarmState`
(M031) into an explainable per-plot crop health assessment: a
`HealthFactor` list carrying measured value, threshold and evidence,
aggregated to a plot `level` (`healthy` / `watch` / `stressed` /
`unknown`) and rolled up to a farm level. It also owns the
**staleness policy** M019 and M031 deliberately deferred.

#### Why This Milestone Exists
M031 made the signals canonical but decision-free; M033 (risk), M034
(recommendations), M037 (disease context) and M048 (dashboard) all
need one shared, auditable answer to "how is this plot doing?" — and
it must be a *rules* engine (deterministic, testable, no model, no
network) so the demo's advice can always be explained line by line.

#### Files Expected to Be Created
- `src/engines/__init__.py`
- `src/engines/health.py`
- `tests/engines/__init__.py`
- `tests/engines/test_health.py`

#### Files Expected to Be Modified
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None. Pure computation over data M019/M031 already expose — no table,
no endpoint, no worker (M048 renders it, M039 aggregates it).

#### External Dependencies
None (pydantic + stdlib).

#### Service Contract
```python
# src/engines/health.py
HEALTH_LEVELS: tuple[str, ...] = ("healthy", "watch", "stressed", "unknown")
FACTOR_STATUSES: tuple[str, ...] = ("ok", "attention", "stress", "unknown")

STALE_AFTER_SECONDS: dict[str, int] = {   # THE staleness policy (M019 deferred it)
    "weather": 86_400,                    # 24 h - in-situ / current-hour feed
    "soil": 86_400,                       # 24 h - in-situ probe
    "satellite": 7_776_000,               # 90 d - 16-day composite plus the
}                                         # 47-day NASA latency M027 measured

@dataclass(frozen=True)
class CropProfile:                        # per-crop thresholds (demo agronomy)
    ndvi_watch: float = 0.40              # below -> attention
    ndvi_stress: float = 0.25             # below -> stress
    moisture_attention_min: float = 30.0  # % plant-available water
    moisture_stress_min: float = 20.0
    moisture_attention_max: float = 70.0  # waterlogging
    moisture_stress_max: float = 85.0
    ph_attention_min: float = 5.8
    ph_stress_min: float = 5.0
    ph_attention_max: float = 7.2
    ph_stress_max: float = 7.8
    nitrogen_attention_min: float = 40.0  # kg/ha available N
    nitrogen_stress_min: float = 20.0
    # crop-agnostic constants, never overridden in M032:
    #   temperature: attention outside [10, 35] C, stress outside [5, 40] C
    #   rainfall:    attention > 30 mm/day,       stress > 60 mm/day

CROP_PROFILES: dict[str, CropProfile]     # key = crop.lower()
    # "maize": moisture 35/25, nitrogen 50/20, ph 5.8-7.2
    # "wheat": moisture 30/20, nitrogen 40/20, ph 6.0-7.0
    # "beans": moisture 35/25, nitrogen 30/10 (legume N fixation), ph 6.0-7.5
DEFAULT_CROP_PROFILE: CropProfile         # unknown/absent crop -> this

class HealthFactor(BaseModel):
    name: str                 # planting | ndvi | soil_moisture | soil_ph |
                              # nitrogen | air_temperature | rainfall
    status: str               # FACTOR_STATUSES
    measured: float | None    # normalized value the rule saw (None = unusable)
    detail: str               # "soil moisture 18.0% < 25.0% (maize)"

class PlotHealth(BaseModel):
    plot_id: uuid.UUID
    name: str
    crop: str | None
    growth_stage: str | None
    days_since_planted: int | None
    level: str                # HEALTH_LEVELS
    factors: list[HealthFactor]   # always all 7, fixed order
    factors_evaluated: int     # status != unknown
    factor_count: int          # == 7
    computed_at: datetime

class FarmHealth(BaseModel):
    farm_id: uuid.UUID
    level: str                # worst plot level; "unknown" with no plots
    plots: list[PlotHealth]
    plot_count: int
    stale_families: list[str] # families past STALE_AFTER_SECONDS, sorted
    computed_at: datetime

def assess_plot_health(plot: PlotStateView, signals: NormalizedSignals, *,
                       now: datetime | None = None) -> PlotHealth

def assess_farm_health(state: NormalizedFarmState, *,
                       now: datetime | None = None) -> FarmHealth
```

#### Decisions
- **New package `src/engines/`** (peer of `src/providers`,
  `src/ingestion`, `src/services`): pure deterministic computation,
  zero I/O — `src/services/` stays the I/O layer. M033/M034/M039 land
  here too.
- **Seven factors, fixed order:** `planting`, `ndvi`, `soil_moisture`,
  `soil_ph`, `nitrogen`, `air_temperature`, `rainfall`. Every factor is
  always emitted (an unusable one is `unknown`, never omitted) so the
  dashboard shows what is *missing* as well as what is wrong. Wind and
  humidity are deliberately excluded: their damage is event-based and
  cannot be ruled on from a daily aggregate.
- **Aggregation gates on planting, then takes the worst signal
  factor**: no crop state or a future planting date → `unknown`
  (nothing is growing, so there is no health to report); otherwise
  `stress` → `stressed`, `attention` → `watch`, all `ok` → `healthy`,
  and no evaluated signal factor → `unknown`. Planting alone never
  proves health: a registered plot whose three signal families are all
  missing is `unknown`, not `healthy`. Explainability beats averaging —
  every level traces back to exactly one factor detail.
- **Staleness policy lives here (finally decided):** a family older
  than `STALE_AFTER_SECONDS` makes its factors `unknown` (we do not
  judge health from data we have declared untrustworthy) and is
  reported in `stale_families`. The satellite threshold is 90 days,
  not 16 — M027 measured 47-day NASA latency at Nairobi, so a 16/30-day
  threshold would declare every real reading stale.
- **Signals are farm-level, plots are plot-level** — weather, soil and
  NDVI all come from the farm centroid (M023/M026/M029). Per-plot
  variation therefore comes *only* from crop profile + planting date;
  two plots with the same crop on one farm score identically.
  Documented limitation, not hidden: downsampling a scene to plots
  needs per-plot geometry + raster access (no milestone asks for it).
- **Crop profiles are keyed case-insensitively** (`"Maize"` →
  `maize`, as M018/M020 tests write crops) and fall back to
  `DEFAULT_CROP_PROFILE`, because `crop` is free text (M018) with no
  crop registry. Thresholds are *demo agronomy*, documented as such —
  constants, not expertise.
- **Stages and future plantings:** `growth_stage` /
  `days_since_planted` are reported for context but do not move
  thresholds in M032 (stage-aware curves are a later refinement). A
  plot with no crop state, or planted in the future, assesses to
  `unknown` with a `planting` factor explaining why — nothing is
  growing yet.
- **Rainfall is judged on `rainfall_mm_per_day`** (M031's profile
  conversion). Unknown source → conversion is `None` → factor is
  `unknown` with "rainfall window unknown": the honest consequence of
  M031's never-guess rule.
- **Determinism:** same input + same `now` → identical output; every
  `detail` string uses fixed precision. No clock reads beyond the
  injectable `now`.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/engines/__init__.py` package doc + exports; `health.py`
   (constants, `CropProfile`, DTOs, factor rules, aggregation).
3. `tests/engines/` (pure unit, no DB — no `_db` fixture needed).
4. Gate, docs, state, two commits (implementation + hash record).

#### Testing Criteria
`tests/engines/test_health.py` (pure unit, DB-free):
- [x] fresh signals + "Maize" → `healthy`, all 7 factors `ok`,
  `factors_evaluated == 7`, case-insensitive profile lookup.
- [x] ndvi 0.35 → `watch` (`ndvi` factor `attention`, detail names the
  threshold); ndvi 0.20 → `stressed`.
- [x] aggregation: worst factor wins (stress beats attention); planting
  gates the verdict (no crop state / future date → `unknown`);
  crop registered but every signal family absent → `unknown`; empty
  plot list → farm `unknown`.
- [x] staleness: satellite age 91 d → `ndvi` unknown + `stale_families`
  `["satellite"]`; weather age 25 h → `air_temperature`/`rainfall`
  unknown; missing `observed_at` (age `None`) → unknown.
- [x] unusable data → unknown: family absent, `rainfall_mm_per_day` None
  (unknown source), non-numeric/None values.
- [x] bounds per rule: moisture 18 → stress, 28 → attention, 75 →
  waterlog attention, 90 → stress; ph 5.6 → attention, 4.9 → stress;
  nitrogen 35 → attention, 15 → stress; temperature 42 → stress, 8 →
  attention; rainfall 45 mm/day → attention, 70 → stress.
- [x] crop profiles: maize/wheat/beans differ on the same signals; unknown
  crop ("Sorghum") uses `DEFAULT_CROP_PROFILE`.
- [x] `planting` factor: no crop state → `unknown` + detail; `planted_on`
  in the future → `unknown` + detail; both never raise.
- [x] determinism: same `NormalizedFarmState` + `now` twice → equal models.
- [x] rollup: farm level == worst plot level; `stale_families` sorted.

#### Verification Commands
```bash
uv run pytest tests/engines -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No API endpoint (M047/M048), no persistence of results (M039/M041
call it in-process), no risk scoring (M033), no recommendations
(M034), no disease logic (M036/M037), no DB access or queries (it
takes an already-assembled `NormalizedFarmState`), no per-plot
satellite/soil downscaling, no machine learning, no stage-dependent
thresholds.

#### Verification & Notes (added on completion)
- Gate PASSED (2026-09-29, live dev DB on 65432): `ruff format --check`
  OK (113 files), `ruff check` OK, `mypy` OK (110 source files),
  `pytest` **505 passed / 0 skipped** (467 prior + 38 new in
  `tests/engines/test_health.py`); `bandit -r -ll src workers` = 0
  findings; `pip-audit` = no known vulnerabilities (no dependency
  added).
- **No live check by design:** the engine is a pure function over
  data M019/M031 already give it — no network, no DB, no clock beyond
  the injectable `now`.
- **Deviation (spec fixed during implementation, rule 6):** the draft
  aggregation ("worst non-unknown factor") would have called a plot
  with *no signals at all* `healthy` because `planting` was `ok`.
  Changed to *planting gates the verdict, then the worst signal factor
  decides*, so missing data can never masquerade as health; the
  Decisions section and testing criteria were rewritten to match
  before this milestone was closed.
- **Deviation:** NDVI evidence is formatted at 2 dp (`_fmt_ndvi`) —
  one decimal rendered `0.2 < 0.2`, which is not evidence.
- **Finding:** "no reading" and "window unknown" are different
  unknowns and now say so (`no rainfall reading` vs `rainfall window
  unknown for this source`); collapsing them would hide whether M031's
  profile lookup failed or the provider simply omitted the field.
- **Finding:** per-plot scores only differ by crop profile and
  planting date — every signal comes from the farm centroid, so two
  "Maize" plots on one farm are always identical. Recorded as a
  limitation of the whole provider/ingestion chain, not a bug here.
- **Finding:** the 90-day satellite staleness threshold is *derived
  from a measurement* (M027: 47-day NASA latency + 16-day composite),
  and `test_fresh_satellite_threshold_is_not_16_days` pins the
  boundary (90 days − 1 s stays fresh) so nobody tightens it back to
  16 days and turns every real reading into `unknown`.
- New package `src/engines/` (with `tests/engines/`): pure
  computation, peer of `src/services`. M033/M034/M039 are expected to
  land here rather than in `src/services`.

### M033 — Farm risk engine (deterministic scoring)

**Priority:** P0 **Depends On:** M031, M032
**Status:** done

#### Objective
A deterministic farm-level risk score (0–100, band `low` / `moderate`
/ `high`) assembled from named, individually-scored risk items:
hazards mapped from M032's health factors, plus visibility penalties
for stale or missing signal families. Pure, explainable, additive —
`FarmRisk.items` shows every point in the total.

#### Why This Milestone Exists
Health says what a plot *is*; risk says what the farm *faces*. M048
visualises health and risk side by side, M039 aggregates risk into
decisions and M041 turns it into advice — all three need one shared,
auditable number instead of three different heuristics.

#### Files Expected to Be Created
- `src/engines/risk.py`
- `tests/engines/test_risk.py`

#### Files Expected to Be Modified
- `src/engines/health.py` (export the two crop-profile helpers)
- `src/engines/__init__.py` (exports)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None. No table, no endpoint, no persistence.

#### External Dependencies
None (pydantic + stdlib).

#### Service Contract
```python
# src/engines/risk.py
RISK_BANDS: tuple[str, ...] = ("low", "moderate", "high")
BAND_THRESHOLDS: tuple[int, int] = (25, 60)   # score <25 low, <60 moderate, else high
MAX_SCORE: int = 100

SEVERITY_POINTS: dict[str, int] = {"attention": 15, "stress": 30}
MISSING_SIGNAL_POINTS: int = 15     # per signal family never ingested
STALE_SIGNAL_POINTS: int = 10       # per signal family past STALE_AFTER_SECONDS
UNREGISTERED_PLOT_POINTS: int = 10  # per plot with no crop state

RISK_ORDER: tuple[str, ...] = (     # items are emitted in this order, zero-point
    "drought", "waterlogging",       # items are omitted
    "heat", "cold", "heavy_rain",
    "nutrient_shortfall", "soil_ph", "low_vigor",
    "unregistered_plots", "stale_signals", "missing_signals",
)

def risk_band(score: int) -> str

class RiskItem(BaseModel):
    name: str          # one of RISK_ORDER
    points: int        # its contribution to the total
    detail: str        # deterministic evidence, e.g. "soil moisture 18.0% < 35.0% (maize)"

class FarmRisk(BaseModel):
    farm_id: uuid.UUID
    score: int                 # min(100, sum(item.points))
    band: str                  # RISK_BANDS
    items: list[RiskItem]      # non-zero contributions only, RISK_ORDER order
    hazard_readings_evaluated: int   # usable hazard readings (max 6 per plot)
    hazard_readings_total: int       # 6 * plot_count
    plot_count: int
    computed_at: datetime

def assess_farm_risk(state: NormalizedFarmState, health: FarmHealth, *,
                     now: datetime | None = None) -> FarmRisk
    # ValueError when health.farm_id != state.view.farm_id (caller bug)
```

#### Decisions
- **Risk is a mapping over M032's output, not a second set of rules.**
  Every hazard reads a `HealthFactor` M032 already judged (status +
  measured + the plot's `CropProfile`), so there is exactly one place
  where "what does 18 % soil moisture mean". Only two things come
  straight from M031's normalized state: which families are *missing*.
- **Hazard (conditions) and blind spots (visibility) are the only
  score components** — deliberately *not* an "impact" component. The
  farm's health levels are the crop's response to these same
  conditions, so scoring them again would count one problem twice;
  M048 shows health next to risk for exactly that reason.
- **Additive and capped:** severity points (attention 15, stress 30)
  with `max()` per hazard across plots, plus 15/10 per missing/stale
  family and 10 per unregistered plot; `score = min(100, sum)`. Every
  point appears as an item, so the number can always be re-derived by
  hand — the definition of deterministic scoring.
- **Bands: `low` < 25, `moderate` < 60, `high` ≥ 60** — one attention
  (15) stays `low`, one stress (30) or two attentions reach
  `moderate`, two stresses reach `high`.
- **Crop profile is per plot**, so the farm's most vulnerable crop
  drives each hazard (two plots → worst case wins), matching how
  `FarmHealth` rolls up.
- **Visibility is real risk:** a family never ingested costs more
  (15) than a stale one (10), and a plot without crop state costs 10 —
  you cannot manage what the platform cannot see.
- **Zero is a legitimate answer:** fresh signals, no hazard, every
  plot registered → `score == 0`, `band == "low"`, `items == []`.
- **Guard against caller mistakes:** passing a `FarmHealth` built for
  another farm raises `ValueError` rather than silently scoring the
  wrong data.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Export `crop_profile_for` / `crop_label_for` from `health.py`
   (renamed from the private helpers M032 used internally).
3. `risk.py`: constants, `RiskItem`/`FarmRisk`, hazard mapping,
   visibility penalties, banding.
4. `tests/engines/test_risk.py` (pure unit, no DB).
5. Gate, docs, state, two commits (implementation + hash record).

#### Testing Criteria
`tests/engines/test_risk.py` (pure unit, DB-free):
- [x] fresh signals, every plot registered, no hazard → `score == 0`,
  `band == "low"`, `items == []`, readings `6 × plot_count`.
- [x] one attention (e.g. soil moisture 28 % on maize) → drought
  15 points → `band == "low"`; one stress (18 %) → 30 → `"moderate"`.
- [x] direction matters: moisture 90 % → `waterlogging`, not `drought`;
  temp 42 °C → `heat`, 8 °C → `cold`; rainfall 70 mm/day →
  `heavy_rain`.
- [x] every hazard maps: ndvi 0.20 → `low_vigor`, nitrogen 15 →
  `nutrient_shortfall`, pH 4.9 → `soil_ph`, all 30 points.
- [x] worst-case across plots: maize stressed + wheat fine → hazard
  counted once at the higher point value.
- [x] visibility: missing soil family → `missing_signals` 15;
  weather stale 25 h → `stale_signals` 10; plot without crop state →
  `unregistered_plots` 10.
- [x] cap: enough stress hazards → `score == 100`.
- [x] bands: `risk_band(24/25/59/60)` → `low/moderate/moderate/high`.
- [x] item order follows `RISK_ORDER`; zero-point items are absent.
- [x] determinism: same inputs twice → equal models; mismatched
  `farm_id` → `ValueError`.

#### Verification Commands
```bash
uv run pytest tests/engines -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No weighting model, no probability/likelihood math (this is a
deterministic tally, not a forecast), no per-plot risk output (farm
level only; plot detail comes from M032's health), no persistence, no
API endpoint, no recomputation of M032's thresholds, no LLM.

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED — 532 passed / 0 skipped
  (115 files formatted, ruff clean, mypy clean on 112 sources). New
  coverage: `tests/engines/test_risk.py` = 27 tests; engines total 65.
- **Security:** `bandit -r -ll src workers` 0 findings; `pip-audit`
  clean (only the local `agrin` package skipped). No new dependencies.
- **Files:** new `src/engines/risk.py`, `tests/engines/test_risk.py`;
  `src/engines/health.py` exports `crop_profile_for` / `crop_label_for`
  (renamed from `_profile_for` / `_label_for`); `src/engines/__init__.py`
  re-exports both plus the risk symbols.
- **Design confirmation:** risk items reuse M032's `HealthFactor.detail`
  verbatim as their `detail` — no threshold, label or formatting is
  duplicated in the risk layer; the only new strings are the three
  visibility details.
- **Findings:**
  - Staleness beats hazard detection when one doc serves both roles:
    a weather doc 25 h old gives `stale_signals` but its temperature is
    unknown, so it yields no `heat` item. Test uses a stale satellite
    doc instead to assert item *order* while keeping heat live.
  - Visibility-only farm (no families, unregistered plot) = 55 points →
    `moderate`, not `high` — confirms the 60-point band edge needs at
    least one real stress hazard too.
  - Cap test reaches 160 raw points across hazards + stale + missing →
    reported 100; `RISK_ORDER` caps the item list at 11 names.
- **Not built (per spec):** no weights/probabilities, no per-plot risk,
  no persistence, no API — consumers arrive with M048 (dashboard) and
  M039 (decision aggregation).

### M034 — Crop recommendation engine (rule-based)

**Priority:** P0 **Depends On:** M031, M032 (dependency note below)
**Status:** done

#### Objective
Turn the farm's normalized signals and M032's per-plot health verdicts
into a deterministic, flat list of actionable recommendations —
`irrigate`, `apply_nitrogen`, `hold_field_work`, … — one per bad
factor, plus the farm-level data-quality nudges (stale/missing signal
families, unregistered plots) that say *why* advice is thin. Structured
for M039 to aggregate and M041 to phrase.

#### Why This Milestone Exists
Health says what a plot *is*, risk says what the farm *faces* — neither
says what to *do*. M039's decision engine needs one canonical
"recommended actions" input and M041's advisory generation needs the
same list to build its prompt, so the advice a farmer reads has a
single source instead of re-derived rules per endpoint.

#### Files Expected to Be Created
- `src/engines/recommend.py`
- `tests/engines/test_recommend.py`

#### Files Expected to Be Modified
- `src/engines/__init__.py` (exports)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes / API Changes / Frontend Changes
None. No table, no endpoint, no persistence.

#### External Dependencies
None (pydantic + stdlib).

#### Dependency note (documented deviation)
The roadmap listed `Depends On: M031` — that row was written before
M032 existed. Knowing that 18 % soil moisture needs *irrigation* is
exactly M032's agronomy (`CropProfile` thresholds + `crop_profile_for`),
and M033 already set the precedent of reading it rather than restating
it: a second copy of the thresholds would drift the moment a profile
changes. Roadmap row updated to `M031, M032`.

#### Service Contract
```python
# src/engines/recommend.py
RECOMMENDATION_PRIORITY: tuple[str, ...] = ("urgent", "soon", "routine")
RECOMMENDATION_CATEGORIES: tuple[str, ...] = (
    "irrigation", "drainage", "fertility", "soil_amendment",
    "weather_protection", "field_operation", "scouting",
    "record_keeping", "data_quality", "monitoring",
)

RECOMMENDATION_ORDER: tuple[str, ...] = (   # canonical code order;
    "set_crop_plan", "irrigate", "improve_drainage",   # doubles as the
    "apply_nitrogen", "raise_ph", "lower_ph",          # tie-break sort key
    "heat_protection", "frost_protection", "hold_field_work",
    "inspect_crop", "refresh_signals", "ingest_missing_signals",
    "continue_as_planned",
)
RECOMMENDATION_SPECS: dict[str, tuple[str, str]] = {}  # code → (category, title)

class Recommendation(BaseModel):
    code: str                    # one of RECOMMENDATION_ORDER
    category: str                # one of RECOMMENDATION_CATEGORIES
    priority: str                # urgent | soon | routine
    title: str                   # short imperative, family interpolated
    detail: str                  # evidence; factor items reuse M032's sentence
    plot_id: uuid.UUID | None    # None = farm-level item
    plot_name: str | None

class FarmRecommendations(BaseModel):
    farm_id: uuid.UUID
    recommendations: list[Recommendation]   # flat, sorted (rule below)
    actionable: int                         # items excluding continue_as_planned
    plot_count: int
    computed_at: datetime

def recommend_farm_actions(
    state: NormalizedFarmState,
    health: FarmHealth,
    *,
    now: datetime | None = None,
) -> FarmRecommendations    # ValueError when health/state farm_ids differ
```

Rule table — one action per M032 factor verdict, **no new thresholds**:

| factor verdict (M032) | code | priority |
|---|---|---|
| moisture < attention_min (drought) | `irrigate` | stress → `urgent`, attention → `soon` |
| moisture > attention_max (waterlogging) | `improve_drainage` | same |
| nitrogen below attention | `apply_nitrogen` | same |
| pH below / above band | `raise_ph` / `lower_ph` | same |
| temperature above / below band | `heat_protection` / `frost_protection` | same |
| rainfall above attention | `hold_field_work` | same |
| ndvi below watch | `inspect_crop` | same |
| plot has no crop state | `set_crop_plan` | `soon` |
| signal family stale (M032's list) | `refresh_signals` (one per family) | `soon` |
| signal family never ingested | `ingest_missing_signals` (one per family) | `soon` |
| plot registered, level `healthy`, no unknown factor | `continue_as_planned` | `routine` |

Sort order: `priority` (`urgent` < `soon` < `routine`), then
`RECOMMENDATION_ORDER` index, then `plot_name` — fully deterministic.

#### Design Decisions
- **Reuse M032's thresholds and evidence, never restate them** — same
  rule as M033: a factor-derived item's `detail` *is* the
  `HealthFactor.detail` sentence, and direction (drought vs
  waterlogging, heat vs cold) comes from the plot's own `CropProfile`.
- **`continue_as_planned` only when `level == "healthy"` *and* every
  factor is known.** A plot whose signals are stale or missing gets no
  reassurance at all (M032's "absence of evidence is never evidence of
  health" — a healthy rollup over three known factors says nothing
  about the blind fourth); the farm-level `refresh_signals` /
  `ingest_missing_signals` items carry the explanation instead.
- **Input shape matches M033** (`state`, `health`, `now`) so M039
  calls three pure functions with one signature. Risk itself is not an
  input — advice must not be pre-scored; M039 combines them.
- **Farm-level for data quality, plot-level for agronomy:** `plot_id is
  None` marks the boundary; each stale or missing family is its own
  item so counts stay meaningful.
- **Flat list, not nested by plot** — the engine owns ordering, not
  grouping; M039/M041/M050 group however they render.
- **Bounded output:** ≤ 7 agronomy items per plot (one per factor) + at
  most one `set_crop_plan`, plus one item per stale/missing family.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `recommend.py`: constants + spec table, DTOs, per-plot factor
   mapping, visibility items, sort, `ValueError` guard.
3. `tests/engines/test_recommend.py` (pure unit, no DB — raw-doc
   builders copied from `test_risk.py`).
4. Gate, docs, state, two commits (implementation + hash record).

#### Testing Criteria
`tests/engines/test_recommend.py` (pure unit, DB-free):
- [x] healthy registered plot, fresh signals → exactly one
  `continue_as_planned` (`routine`), `actionable == 0`.
- [x] attention vs stress → `soon` vs `urgent` for the same code
  (moisture 28 % → `irrigate/soon`, 18 % → `irrigate/urgent`).
- [x] every rule row fires: drought → `irrigate`, waterlogging →
  `improve_drainage`, low N → `apply_nitrogen`, low pH → `raise_ph`,
  high pH → `lower_ph`, heat → `heat_protection`, cold →
  `frost_protection`, heavy rain → `hold_field_work`, low ndvi →
  `inspect_crop`.
- [x] factor-derived `detail` equals M032's factor detail verbatim.
- [x] plot without crop state → `set_crop_plan` and **no**
  `continue_as_planned`.
- [x] stale family → `refresh_signals` (one item per family, `soon`);
  missing family → `ingest_missing_signals`; a plot with unknown
  factors gets no reassurance item.
- [x] one plot with several stresses → several `urgent` items, all
  present, priority order intact.
- [x] sort: `urgent` before `soon` before `routine`; ties by
  `RECOMMENDATION_ORDER` then plot name; two runs identical.
- [x] farm-level items have `plot_id is None`; plot items carry id and
  name.
- [x] every `code`/`category`/`priority` is drawn from the documented
  tuples; empty farm → `recommendations == []`, `plot_count == 0`.
- [x] mismatched `farm_id` → `ValueError`.

#### Verification Commands
```bash
uv run pytest tests/engines -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No thresholds of its own (health owns agronomy), no risk scoring
(M033), no disease or pest diagnosis (M036/M037), no LLM phrasing or
tone (M041), no persistence and no endpoint (M043+), no weather
*forecast* logic (observations only), no stage-aware curves (M032's
documented limitation), no scheduling or cron.

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED — 554 passed / 0 skipped (117
  files formatted, ruff clean, mypy clean on 114 sources). New
  coverage: `tests/engines/test_recommend.py` = 22 tests; engines
  total 87 (health 38, risk 27, recommend 22).
- **Security:** `bandit -r -ll src workers` 0 findings; `pip-audit`
  clean (only the local `agrin` package skipped). No new dependencies.
- **Files:** new `src/engines/recommend.py`, `tests/engines/
  test_recommend.py`; `src/engines/__init__.py` re-exports the four
  constants, both DTOs and `recommend_farm_actions`.
- **Design confirmation:** `detail` strings for agronomy items are
  M032's `HealthFactor.detail` verbatim (asserted), so advice and
  evidence can never drift; direction/thresholds come from the plot's
  `CropProfile` and `TEMPERATURE_ATTENTION` — zero new thresholds.
- **Findings:**
  - The `blind` guard is doing real work: with *farm-wide* signals,
    one stale family leaves every plot with an unknown factor, so no
    plot can be told "no action needed" while the farm is blind — even
    when M032's rollup still reads `healthy` (three known factors, one
    unknown). Health and advice therefore disagree *by design* in that
    case, and M041 should say why rather than restate `healthy`.
  - Signals being farm-level means plot-level contrast can only come
    from crop profiles: the ordering test contrasts maize (attention at
    32 %) with wheat (fine at 32 %) instead of differing soil docs.
  - `continue_as_planned` and agronomy items never coexist on one
    plot (the level gate and the blind gate are complements), so
    `actionable` equals the agronomy-plus-data-quality count.
- **Dependency deviation (recorded in the spec):** roadmap listed
  `Depends On: M031` from before M032 existed; the engine needs
  `CropProfile` thresholds and now reads them like M033 does. Row
  updated to `M031, M032`.
- **Doc corrections along the way:** stale `**Status:** in-progress`
  lines on M014 and M033 flipped to `done`.
- **Not built (per spec):** no thresholds of its own, no risk scoring,
  no disease logic, no LLM phrasing, no persistence/endpoint, no
  forecast logic, no stage-aware curves.

### M035 — Image upload endpoint (MIME/size/decompression limits)

**Priority:** P0 **Depends On:** M016
**Status:** done

#### Objective
`POST /api/v1/farms/{farm_id}/plots/{plot_id}/images` (multipart) that
accepts one photo under hard limits — ≤ 5 MB bytes, ≤ 25 megapixels,
JPEG/PNG/WebP confirmed by **magic bytes, never the client's
`Content-Type`** — stores it under a server-generated random filename,
records a `plot_images` row, and serves it back with `GET`
(`.../images/{image_id}`) plus a `.../images` list, all under M016's
ownership matrix.

#### Why This Milestone Exists
M036's disease provider needs a real file on disk to read, M037 needs
an image id to attach a diagnosis to, and M049 shows the picture in a
browser. Upload is the only place in the system where **untrusted
bytes** enter, so its limits get a milestone of their own (the roadmap
named it that way) instead of hiding inside the disease feature.

#### Files Expected to Be Created
- `src/models/plot_image.py` (ORM model)
- `alembic/versions/0010_plot_images.py` (hand-written migration)
- `src/api/v1/images.py` (router)
- `tests/api/test_images.py`

#### Files Expected to Be Modified
- `src/models/__init__.py`, `src/api/v1/__init__.py` (registration)
- `src/core/errors.py` (413/415/422 subclasses for image failures)
- `src/core/config.py` (`upload_dir`, `upload_max_bytes`,
  `upload_max_pixels`)
- `pyproject.toml` (**two new runtime deps:** `python-multipart`,
  `Pillow`)
- `.gitignore` (ignore `var/`)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
New table `plot_images` (migration `0010`, hand-written per the
standing rule): `id` UUID PK, `plot_id` UUID FK → `plots.id`
`ON DELETE CASCADE`, `uploaded_by` UUID FK → `users.id` (nullable —
seeds/workers may upload), `original_name` String(255) nullable
(display only, basename-capped), `content_type` String(40) (**sniffed**),
`size_bytes` Integer, `stored_name` String(64) (server-generated
`{uuid}.{ext}` — no path segments, no user input), `created_at`
timestamptz default now(). Index on `plot_id`.

#### API Changes
| Verb | Route | Success | Failures |
|---|---|---|---|
| POST | `/api/v1/farms/{farm_id}/plots/{plot_id}/images` | 201 `ImageRead` | 401 anon · 403 officer · 404 non-owner farmer / unknown plot · 413 `payload_too_large` (> 5 MB) · 413 `image_too_large` (> 25 MP) · 415 `unsupported_media_type` · 422 `invalid_image` (corrupt) |
| GET | `.../images/{image_id}` | 200 file bytes | 401 · 403 · 404 (image not in that plot → 404, no oracle) |
| GET | `.../images` | 200 `ImageList` | 401 · 403 · 404 |

Authz reuses `_authorized_plot(for_write=)` from `plots.py` (private
import — the established pattern): write verbs owner/admin, reads any
of owner/admin/officer, non-owner farmer → 404.
`ImageRead = {id, plot_id, content_type, size_bytes, original_name,
created_at, url}` where `url` is the GET path (what M049 renders).

#### External Dependencies (new, pinned, why)
- `python-multipart` — FastAPI parses `multipart/form-data` and
  produces `UploadFile` only with it; no alternative without rolling
  our own parser (rejected: security-sensitive reinvention).
- `Pillow` — magic-byte sniffing (`Image.open` reads the header only),
  explicit pixel-dimension check before any decode, `verify()` to
  reject truncated/corrupt payloads. The stdlib has no image decoder.
Both pinned exactly like every other runtime dep; `bandit` +
`pip-audit` re-run before commit.

#### Service Contract
```python
# src/core/config.py
upload_dir: Path = Path("var/uploads")  # gitignored; tests point it at tmp_path
upload_max_bytes: int = 5 * 1024 * 1024  # 5 MB
upload_max_pixels: int = 25_000_000  # 25 MP, checked pre-decode

# src/api/v1/images.py
ALLOWED_FORMATS: dict[str, str] = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}


class ImageRead(BaseModel):
    id: uuid.UUID
    plot_id: uuid.UUID
    content_type: str  # sniffed: image/jpeg | image/png | image/webp
    size_bytes: int
    original_name: str | None
    created_at: datetime
    url: str  # GET path for the frontend


class ImageList(BaseModel):
    items: list[ImageRead]
    total: int
```

#### Security / Validation Decisions (the point of this milestone)
1. **Authz before bytes** — 401/403/404 decisions never touch the body.
2. **Size first, parse second:** `read(max_bytes + 1)` → 413, so a
   giant body never gets buffered whole.
3. **Sniff, don't trust:** `Image.open(BytesIO(data)).format` must be
   `JPEG`/`PNG`/`WEBP` → else 415. The stored `content_type` comes
   from the sniff, not the request (a PNG sent as `image/jpeg` is
   stored as `image/png`).
4. **Pixel cap before decode:** header width×height > 25 MP → 413
   `image_too_large` (this is the decompression-bomb guard; Pillow's
   own `MAX_IMAGE_PIXELS` threshold is far higher and only warns).
5. **`verify()`** catches truncated/corrupt payloads → 422
   `invalid_image`.
6. **Storage:** `{uuid4}.{ext}` under `settings.upload_dir`
   (mkdir'd on demand). User filename never touches the path;
   `original_name` is basename-stripped and length-capped, kept for
   display only. Random uuid4 names are unguessable and traversal-proof.
7. **Serving:** `FileResponse` with the sniffed content type plus
   `X-Content-Type-Options: nosniff`; same ownership check as reads.
8. **No re-encode, no EXIF strip** (documented: bytes are stored as
   received after validation; virus scanning is out of scope).

#### Design Decisions
- **Nested under plots like everything else** — the picture belongs to
  a plot, and reusing `_authorized_plot` gives the exact authz matrix
  (and 404 no-oracle behaviour) for free instead of re-deriving it.
- **A table, not bare files** — M037 needs to reference an image id,
  M049 needs to list them, and ownership queries need rows; the file
  path is an implementation detail of the row.
- **Settings-driven limits** — tests and future deployments retune
  bytes/pixels/directory without code changes; defaults are the
  documented demo limits.
- **Multipart + Pillow are runtime deps** — the endpoint cannot exist
  without them; recorded as an explicit addition (precedent D8's
  discipline: pin exactly, audit, state it).

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. Add the two dependencies (pinned) to `pyproject.toml`.
3. Model + migration `0010`; verify `alembic upgrade head` and
   `alembic check` are clean; `alembic downgrade base && upgrade head`
   round-trips (migration test covers it).
4. Errors + config additions.
5. Router (upload/list/get) with the validation pipeline.
6. `tests/api/test_images.py`.
7. Gate, bandit, pip-audit, docs, state, two commits.

#### Testing Criteria
`tests/api/test_images.py` (mirrors `test_plots.py` fixtures; needs the
dev DB, skips without it):
- [x] upload happy path: 201, `ImageRead` fields correct, row exists,
  file exists under `upload_dir` with a random server-generated name,
  `original_name` preserved for display.
- [x] sniff is authoritative: PNG bytes declared as `image/jpeg` are
  stored as `image/png`.
- [x] GET round trip: bytes identical to upload, sniffed content type,
  `X-Content-Type-Options: nosniff` present.
- [x] list returns the plot's images with `url`, `total`.
- [x] authz matrix on both verbs: anon → 401, officer → 403,
  non-owner farmer → 404, owner/admin → 2xx; unknown plot → 404;
  another plot's image id under this plot's URL → 404.
- [x] limits: payload > 5 MB → 413 `payload_too_large`; a small PNG
  whose header declares > 25 MP → 413 `image_too_large`; text/GIF →
  415 `unsupported_media_type`; truncated JPEG → 422 `invalid_image`.
- [x] deleting a plot removes its image rows (FK CASCADE).
- [x] no file lands outside `settings.upload_dir` (monkeypatched to
  `tmp_path` in tests).

#### Verification Commands
```bash
uv run alembic upgrade head && uv run alembic check
uv run pytest tests/api/test_images.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No image re-encoding, resizing, thumbnails or EXIF stripping; no virus
scanning; no S3/CDN or async upload job; no delete endpoint (orphaned
files after a plot delete are a documented limitation, cleaned up in a
later milestone); no disease classification or assessment (M036/M037);
no rate limiting (M055); no frontend (M049).

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED — 564 passed / 0 skipped (121
  files formatted, ruff clean, mypy clean on 118 sources). New
  coverage: `tests/api/test_images.py` = 10 tests.
- **Security:** `bandit -r -ll src workers` 0 findings; `pip-audit`
  clean *including the two new deps* (only the local `agrin` package
  skipped). `uv run alembic check` reports no drift; migration tests
  round-trip `0010`.
- **New runtime dependencies (pinned):** `python-multipart==0.0.32`
  (FastAPI's multipart parsing) and `pillow==12.3.0` (sniff, header
  pixel check, `verify()`). Added via `uv add`, repinned to `==` per
  repo convention — flagged because D8's precedent treats dependency
  changes as explicit, recorded decisions.
- **Files:** new `src/models/plot_image.py`,
  `alembic/versions/0010_plot_images.py`, `src/api/v1/images.py`,
  `tests/api/test_images.py`; modified `src/models/__init__.py`,
  `src/api/v1/__init__.py`, `src/core/errors.py` (+413 `payload_too_large`
  / +413 `image_too_large` / +415 `unsupported_media_type` / +422
  `invalid_image`), `src/core/config.py` (`upload_dir`,
  `upload_max_bytes`, `upload_max_pixels`), `.gitignore` (`var/`),
  `tests/api/test_idor.py`.
- **Findings:**
  - **The default-deny guard earned its keep:** the IDOR inventory
    test crashed with `KeyError: 'image_id'` on the first run — a new
    route had appeared that its `_bind` helper didn't know. Fixed by
    binding *every* `{param}` with a regex, so the next endpoint can't
    slip through the 401 sweep.
  - **Truncated files are a 500 if you only catch
    `UnidentifiedImageError`.** A JPEG cut in half fails inside
    `Image.open` itself with a bare `OSError("Truncated File Read")`;
    the test caught it (422 expected, 500 received). `_decode` now
    maps header-level `OSError` → 422 `invalid_image`, so corruption at
    *any* depth lands on the same code.
  - **Authz demonstrably precedes body validation:** the inventory test
    POSTs `{}` (JSON) to the multipart route and still gets 401 —
    FastAPI solves security dependencies before the body, so the
    "authz before bytes" rule holds structurally, not by luck.
  - Pixel-cap test writes a 5001×5001 (25.01 MP) PNG in `"1"` mode —
    ~1 KB on disk, 25 MB of pixels: exactly the decompression-bomb
    shape the limit exists for.
  - Orphaned files after a plot delete remain (rows cascade, bytes
    stay in `var/uploads`) — recorded, cleanup is a later milestone.
- **Not built (per spec):** no re-encode/resize/EXIF strip, no virus
  scan, no S3/CDN, no delete endpoint, no disease logic, no rate
  limiting, no frontend.

### M036 — Disease provider interface + demo provider

**Priority:** P0 **Depends On:** M021, M035
**Status:** done

#### Objective
The typed `disease` family contract every disease source must satisfy —
`DiseaseDetection` / `DiseaseCandidate` models, a **crop-linked disease
vocabulary** (`DISEASE_CATALOG`), the abstract
`DiseaseProvider.detect(image: bytes)` and the typed
`get_disease_provider()` accessor — plus a deterministic, network-free
demo implementation registered under `("disease", "demo")` through the
normal M021 registry path.

#### Why This Milestone Exists
M037 must blend a diagnosis with farm state, so it needs one canonical
shape and one canonical vocabulary to blend *against* — crop affinity
lives with the vocabulary, not re-derived per consumer. M038 swaps in a
live model behind the same ABC without touching M037, and M049's
"upload → result" flow starts here: bytes in, structured candidates out.
The family flag (`disease_provider`, M002) and the `KNOWN_FAMILIES`
slot already exist; this milestone fills them.

#### Files Expected to Be Created
- `src/providers/disease.py` (models, catalog, ABC, typed getter)
- `src/providers/disease_demo.py`
- `tests/providers/test_disease.py`

#### Files Expected to Be Modified
- `src/providers/__init__.py` (contract exports + one registration
  import, the established grep-able line)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None. No table, no endpoint, no persistence — detection results become
rows only when an assessment/endpoint milestone asks for them.

#### API Changes
None. The provider is consumed by M037's assessment (and later an
endpoint), not called directly from HTTP.

#### External Dependencies
None (pydantic + stdlib). M035's Pillow is deliberately *not* used
here: the provider receives opaque bytes and never inspects or
transforms pixels (sniffing already happened at upload).

#### Design Decisions
- **Bytes in, models out.** The provider never touches the database or
  the filesystem — the caller reads the file M035 wrote and passes the
  bytes. This keeps providers storage-agnostic (M021 rule) and makes
  the demo trivially unit-testable.
- **The vocabulary is part of the contract.** `DISEASE_CATALOG:
  Final[dict[str, DiseaseSpec]]` maps code → human label + the set of
  crops it plausibly affects (`frozenset` of `maize`/`wheat`/`beans`
  — the M032 crop profiles). M037 down-weights a candidate whose
  catalog crops don't include the plot's crop; defining that here
  means one source of truth instead of a second list in the engine.
  `DiseaseSpec` is a frozen dataclass (`Final` catalog), mirroring
  `CropProfile`'s style in `health.py`.
- **Codes are validated against the catalog** by a pydantic validator
  on `DiseaseCandidate.code` — a live provider (M038) that invents a
  code fails loudly at the model boundary (`ValidationError`, to be
  mapped to `ProviderResponseInvalid` by that milestone), and the demo
  cannot drift either.
- **Confidence is a probability-shaped float in [0, 1]** with the demo
  documenting a narrower honest range (0.30–0.95: a demo model never
  claims certainty it cannot have).
- **An empty `detections` list means "no findings"** — no synthetic
  `healthy` label. M037 owns the healthy wording; the provider only
  reports what it (did not) find.
- **Demo determinism from the payload itself** (`image_seed`: sha256 of
  the bytes) — same photo always yields the same diagnosis, which is
  what makes the demo stable and testable. Documented behavior:
  0–2 candidates, no duplicate codes, 20 % of inputs yield no findings
  (`seed % 5 == 0`), confidence 0.30–0.95.
- **Empty payload → `ValueError`** (caller-bug guard, same doctrine as
  `_demo.check_wgs84`), never `ProviderError` — no upstream was
  contacted. M035's upload pipeline makes it unreachable in practice.
- **No bounding boxes, no crop/resize, no preprocessing** — the demo
  does no vision, and pixels arrive exactly as M035 stored them. If
  M038's live model needs regions or a resized input, it gains
  *optional* fields then; nothing in this contract blocks that.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/providers/disease.py`: models, catalog, ABC, getter.
3. `src/providers/disease_demo.py`: `@register` demo provider.
4. `src/providers/__init__.py`: exports + registration import.
5. `tests/providers/test_disease.py`.
6. Gate, bandit, pip-audit, docs, state, two commits.

#### Testing Criteria
`tests/providers/test_disease.py` (pure unit — no DB, no network):
- [x] registered through the normal settings path: `get_provider("disease")`
  resolves the demo (default flag), typed getter returns
  `DiseaseProvider`, family/mode/name correct, registry caches one
  instance; `get_disease_provider(mode="live")` →
  `ProviderNotRegistered` (M038 not built).
- [x] determinism: same bytes → identical detections; different bytes
  → different result.
- [x] documented ranges over a fixed sweep: confidence within
  0.30–0.95, 0–2 candidates, every code in `DISEASE_CATALOG`, no
  duplicate codes within one result, at least one empty result
  (the no-findings path) and at least one non-empty in the sweep.
- [x] contract validation: unknown `code` → `ValidationError`;
  confidence outside [0, 1] → `ValidationError`; catalog codes all
  construct cleanly.
- [x] caller guard: empty payload → `ValueError`.
- [x] catalog sanity: every entry's crops are a subset of the known
  crop profiles; labels non-empty.

#### Verification Commands
```bash
uv run pytest tests/providers/test_disease.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live model or HTTP call (M038); no assessment, thresholds,
farm-state blend or "healthy" verdict (M037); no endpoint, DB row or
file read (M049's flow consumes M037 first); no image decoding,
resizing or re-encoding; no bounding boxes; no LLM involvement (M040).

### M037 — Context-aware disease assessment (confidence + farm-state blend)

**Priority:** P0 **Depends On:** M036, M019, M032
**Status:** done

#### Objective
A pure engine — `src/engines/disease.py`, peer of M032/M033/M034 —
that turns one plot's `DiseaseDetection` (M036) plus the farm's
digital twin (`NormalizedFarmState`, M019/M031) and health rollup
(`FarmHealth`, M032) into a `DiseaseAssessment`: an ordered candidate
list with **raw → effective confidence** and an evidence trail, and a
plot verdict (`not_detected` / `uncertain` / `suspected` / `detected`).

#### Why This Milestone Exists
A model's raw score alone is not a diagnosis: the same 0.85 means
something different on a maize plot for a wheat-only disease, and
something different again when the canopy reads healthy. M039 needs a
structured disease input alongside health/risk/recommendations, M049
needs verdict + reasons to render, and M041 needs evidence strings to
phrase — one blend, one vocabulary, decided here.

#### Files Expected to Be Created
- `src/engines/disease.py`
- `tests/engines/test_disease.py`

#### Files Expected to Be Modified
- `src/engines/__init__.py` (exports)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None. No table, no endpoint, no persistence — results become rows only
when a milestone that stores assessments asks for them.

#### API Changes
None. Exposure (endpoint) lands with the dashboard milestone that
needs it — same order M032–M034 used (engine first).

#### External Dependencies
None (pydantic + stdlib + existing engine/provider modules).

#### Design Decisions
- **Shape matches the trio:** `assess_disease(state, health, detection,
  plot_id, *, image_id=None, now=None)` → `DiseaseAssessment`. M039
  calls health + risk + recommendations + disease with the same
  `(state, health)` pair; `ValueError` on farm mismatch or unknown
  plot (the established caller-bug guards).
- **Context may only discount, never inflate.** The model saw the
  pixels; farm context can disagree with it but must not *raise* a
  weak score — a blend that boosts would let farm state launder a
  low-confidence guess into `detected`. Two multipliers, applied in
  sequence, `effective = round(min(1, raw × factors), 3)`:
  - **crop affinity ×0.6** — plot's registered crop not in the
    candidate's `DISEASE_CATALOG` crops (catalog is the expert
    knowledge M036 defined; unknown/unregistered crop gets **no**
    discount, only an "affinity unchecked" reason — unregistered
    plots are already flagged by M032/M034 and must not be punished
    twice for the same gap);
  - **healthy canopy ×0.9** — the plot's own M032 level is
    `healthy`; `stressed` / `watch` / `unknown` add no discount (a
    stressed canopy is *consistent* with disease, but consistency is
    not evidence, so it does not boost either).
- **Two thresholds, one ordering.** Candidates sort by effective
  confidence desc, then code (deterministic, like the trio). Verdict
  from the best: empty → `not_detected`; ≥ 0.70 → `detected`;
  ≥ 0.50 → `suspected`; else `uncertain`. Thresholds are named
  module constants (exported), each with a documented rationale
  (0.70 = model and context jointly worth acting on; 0.50 = report to
  a human, do not act automatically).
- **Every discount and threshold leaves an evidence string.**
  `DiseaseCandidateAssessment.reasons` reads like `HealthFactor.detail`
  (M032 precedent): raw score, the crop line, the canopy line, the
  effective score — M041 phrases these verbatim instead of
  re-deriving them.
- **`DiseaseAssessment` carries context for display:** farm_id,
  plot_id/plot_name/crop, the plot's `health_level`, `image_id`
  (optional passthrough — M049 ties the verdict to the photo),
  `source` (which provider said it), `detected_at` (from M036) and
  `computed_at` (injectable `now`).
- **Signal staleness is deliberately *not* part of the blend.** A
  photo diagnosis does not depend on weather/satellite freshness;
  stale signals already surface in M032/M033 and must not double-count
  here.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/engines/disease.py`: models, constants, `assess_disease`.
3. `src/engines/__init__.py`: exports.
4. `tests/engines/test_disease.py`.
5. Gate, bandit, pip-audit, docs, state, two commits.

#### Testing Criteria
`tests/engines/test_disease.py` (pure unit — fixtures build
`NormalizedFarmState`/`FarmHealth` like the trio's tests):
- [x] empty detections → `not_detected`, no candidates, `image_id`
  passthrough (None default and explicit).
- [x] no-discount path: matching crop + `stressed` canopy →
  `detected`, effective == raw, reasons include crop match and no
  multiplier lines.
- [x] crop mismatch ×0.6: raw 0.90 on a maize plot for a
  wheat/beans-only disease → 0.54 → `suspected`, reason names both
  crops and the factor.
- [x] healthy canopy ×0.9: raw 0.75, matching crop, healthy → 0.675 →
  `suspected`.
- [x] combined discounts: 0.90 mismatch + healthy → 0.486 →
  `uncertain`.
- [x] unregistered crop: no discount, reason says affinity unchecked.
- [x] verdict boundaries: effective exactly 0.70 → `detected`;
  exactly 0.50 → `suspected`; 0.499 → `uncertain`.
- [x] ordering: two candidates sorted by effective desc, code asc on
  ties; labels come from `DISEASE_CATALOG`.
- [x] guards: unknown `plot_id` → `ValueError`; `state`/`health`
  farm mismatch → `ValueError`.
- [x] fields: plot identity, `health_level`, `source`, `detected_at`,
  `computed_at == now`.

#### Verification Commands
```bash
uv run pytest tests/engines/test_disease.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No endpoint, DB row or file read (the photo path is M035's, exposure
is M049's); no farm-level disease rollup (M039 aggregates); no
recommendations or actions (M034 owns those — diagnosis only); no
"healthy" label when nothing was found (empty → `not_detected`);
no live model (M038); no thresholds other than the two documented
ones; no signal-staleness multiplier; no LLM (M040/M041).

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED — 594 passed / 0 skipped (126
  files formatted, ruff clean, mypy clean on 123 sources). New
  coverage: `tests/engines/test_disease.py` = 18 tests (engine total
  now 105 across four engines). Bandit 0, pip-audit clean (no new
  deps).
- **Files:** created `src/engines/disease.py`,
  `tests/engines/test_disease.py`; modified `src/engines/__init__.py`
  (8 exports + docstring "four engines"). No DB, no endpoint.
- **Findings:**
  - **"Context may only discount" proved testable:** an explicit
    invariant test (`context_never_inflates_confidence`) sweeps raw ×
    crop × canopy and asserts `effective ≤ raw` — the one property
    that keeps the blend from becoming a confidence laundromat.
  - Catalog labels are title-case (`Rust`), crop names lowercase
    (`maize`) — the first test failure was an expectation mismatch
    between them; reasons read `crop mismatch: Rust typically affects
    beans, wheat, plot grows maize (x0.6)`. Display casing lives in
    the catalog (M036), engines reuse it verbatim.
  - Ordering test initially gave a mismatched candidate the highest
    raw (0.95 × 0.6 = 0.57 < 0.80 matches) — sorted output disagreed
    with the naive expectation. Corrected to cover *both* sort keys:
    effective-desc across discount classes, code-asc on the 0.80 tie.
  - Stressed-canopy fixtures reuse M032's own thresholds (soil
    moisture 10 % < maize stress 25 %) — no parallel universe of test
    values; if M032's profiles change, these tests follow.
  - Verdict boundaries verified *exactly* at 0.70/0.50 (rounding to
    3 decimals before comparison keeps floats honest).
- **M039 note:** the engine exposes `DiseaseAssessment` per plot/image
  only — aggregation across plots is deliberately M039's job, matching
  how M033/M034 consume M032 rather than re-deriving it.
- **Not built (per spec):** no endpoint/DB/file read, no farm rollup,
  no actions, no live model, no extra thresholds, no staleness
  multiplier, no LLM.

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED — 576 passed / 0 skipped (124
  files formatted, ruff clean, mypy clean on 121 sources). New
  coverage: `tests/providers/test_disease.py` = 12 tests. Bandit 0,
  pip-audit clean (no new deps for this milestone).
- **Files:** created `src/providers/disease.py`,
  `src/providers/disease_demo.py`, `tests/providers/test_disease.py`;
  modified `src/providers/__init__.py` (6 contract exports + one
  registration import). No config change — the `disease_provider`
  flag (M002) and the `"disease"` slot in `KNOWN_FAMILIES` (M021)
  already existed waiting to be filled.
- **Findings:**
  - **The catalog-as-contract decision is the load-bearing one.**
    `DISEASE_CATALOG` lives in the provider module but is consumed by
    M037 (crop affinity) and eventually M049 (labels) — a vocabulary
    that travels with the interface, so no consumer ever re-derives
    its own list. If a future milestone needs a disease the catalog
    lacks, the change happens *here*, once.
  - **Contract validation direction:** unknown codes raise pydantic
    `ValidationError` at model construction — the demo cannot drift,
    and M038's live provider must map that error to
    `ProviderResponseInvalid` at its boundary (noted for that spec).
  - Import sorting moved the "concrete providers register themselves"
    comment along with `disease_demo` (isort attaches a preceding
    comment to the *following* import). Accepted ruff's fix; the
    comment now heads the first concrete import, still one grep-able
    line per provider.
  - The 60-input sweep deterministically covers both paths (the
    `seed % 5 == 0` no-findings rule and the detection path) — no
    randomness in CI, as with every other demo provider.
- **Not built (per spec):** no live model (M038), no assessment or
  healthy verdict (M037), no endpoint/DB/file read, no pixel
  processing, no bounding boxes, no LLM.

### M039 — Structured agricultural decision engine (aggregation)

**Priority:** P0 (🔒 human checkpoint — approved 2026-09-30, D9)
**Depends On:** M033, M034, M037
**Status:** done

#### Objective
The aggregation engine — `src/engines/decision.py` — that folds the
four analysis engines into one structured, deterministic
`FarmDecision`: M032 health rollup, M033 risk score/band, M034's
canonical action list, and M037's per-plot disease verdicts, plus
disease-derived actions, a single farm-level **stance**
(`routine` / `monitor` / `act_now`), and the data-gap caveats M041
must surface. Signature:

```python
def decide_farm(
    state: NormalizedFarmState,
    health: FarmHealth,
    risk: FarmRisk,
    recommendations: FarmRecommendations,
    disease: Sequence[DiseaseAssessment] = (),
    *,
    now: datetime | None = None,
) -> FarmDecision: ...
```

#### Why This Milestone Exists
M041 must phrase one advisory (not four reports), M043 serves one
answer, M044 re-runs "the pipeline" hypothetically, and M050 renders
one verdict — every consumer needs a *single* structured input with a
*single* headline call. This is the milestone the roadmap flagged
`P0 ??` and 🔒: it decides how the platform decides, so the human
approved it explicitly (decision D9).

#### Files Expected to Be Created
- `src/engines/decision.py`
- `tests/engines/test_decision.py`

#### Files Expected to Be Modified
- `src/engines/__init__.py` (exports)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None. No table, no endpoint, no persistence — the decision is computed
on demand (advisory endpoint M043, what-if M044).

#### API Changes
None (M043 exposes advisory text built from this).

#### External Dependencies
None (pydantic + stdlib + the four engine modules).

#### Design Decisions
- **Aggregation, not re-computation.** The four engines' outputs are
  *parameters*, already computed by the caller — M039 adds no
  thresholds of its own and never re-derives evidence. This is what
  makes M044's what-if a clean orchestration (perturb state → re-run
  the four → re-aggregate) and keeps this milestone honest to its
  title: "aggregation".
- **One guard family:** `ValueError` if any input's `farm_id`
  disagrees with `state.view.farm_id` (message names the artifact, as
  M033 established), and `ValueError` for a disease assessment whose
  plot is not in the state.
- **Recommendations pass through verbatim.** Each M034
  `Recommendation` becomes a `DecisionAction` with
  `origin="recommendation"` and identical
  code/category/priority/title/detail/plot fields — evidence reuse by
  copy, not re-derivation.
- **Disease becomes three decision-owned action codes** (M039
  vocabulary, distinct from M034's so nothing double-lists):
  `treat_disease` (urgent, category `disease_control`) for a plot's
  worst verdict `detected`, `verify_disease` (soon, `scouting`) for
  `suspected`, `monitor_disease` (routine, `monitoring`) for
  `uncertain`; `not_detected` counts but emits nothing. Titles name
  the disease label and plot; `detail` is the candidate's
  `reasons` joined with `"; "` — M041 phrases them verbatim (M032/M034
  precedent). `image_id` (M037 passthrough) rides along for M049
  linking. Note: `disease_control` is a **new category**, owned by
  M039 (documented deviation from M034's category list, which stays
  untouched).
- **Worst verdict wins per plot.** Multiple assessments per plot (one
  per photo) collapse by severity (`DISEASE_VERDICTS` order) then
  latest `detected_at`; one action per plot, counts are per plot with
  all four verdict keys present (zeros included — deterministic
  shape).
- **Stance is three documented rules, no new thresholds:**
  `act_now` if risk band `high` OR any urgent action OR any plot
  `detected`; else `monitor` if risk band `moderate` OR any soon
  action OR any plot `suspected`/`uncertain`; else `routine`. Blind
  farms can never claim `routine`, because M034 already emits
  `soon`-priority data-quality actions when signals are missing or
  stale — the stance inherits that guard instead of re-inventing it.
- **Data gaps travel with the decision:** `stale_families` (M032)
  and `plots_with_unknown_factors` (any factor `factors_evaluated <
  factor_count`) give M041 its mandatory caveats.
- **Ordering is total and boring:** priority (M034's
  urgent/soon/routine) → origin (`disease` before `recommendation` —
  photo evidence is specific) → code → plot name (farm-level last) →
  plot id. Ties impossible; M044 re-runs stay byte-identical.

#### Implementation Steps
1. Spec (here), roadmap → in-progress (priority `??` resolved to
   P0 with the approval recorded as D9).
2. `src/engines/decision.py`: models, stance, aggregation.
3. `src/engines/__init__.py`: exports.
4. `tests/engines/test_decision.py` (end-to-end over the real four
   engines — the same composition M044 will re-run).
5. Gate, bandit, pip-audit, docs, state, two commits.

#### Testing Criteria
`tests/engines/test_decision.py` (pure unit; fixtures drive the real
M031→M037 pipeline like this milestone's consumers will):
- [x] clean farm → `routine`, empty-or-routine actions, all four
  disease verdict counts present (zeros when no assessments).
- [x] each stance trigger in isolation: urgent action → `act_now`;
  plot `detected` → `act_now`; moderate risk alone → `monitor`;
  `suspected`/`uncertain` disease → `monitor`; high risk → `act_now`.
- [x] blind farm (no signals) never yields `routine` (M034's
  data-quality actions floor it at `monitor`).
- [x] merged ordering: urgent disease action before urgent
  recommendation; verbatim passthrough of a recommendation's fields.
- [x] disease action: worst verdict per plot (suspected then detected
  → one `treat_disease`), `detail` equals the joined `reasons`,
  title carries label + plot name, `image_id` preserved.
- [x] counts: per-plot verdict counts, action_counts keyed
  urgent/soon/routine, `plots_with_unknown_factors` reflects
  factor-blind plots.
- [x] guards: farm mismatch on each of the four inputs →
  `ValueError` naming the artifact; assessment for a plot outside the
  state → `ValueError`.
- [x] summary echo: health_level, risk_score, risk_band,
  stale_families, plot_count, `computed_at == now`; no clock read
  when `now` is given; same inputs → identical decision.

#### Verification Commands
```bash
uv run pytest tests/engines/test_decision.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No thresholds invented here (the four engines own theirs); no
re-derivation of any evidence string; no advisory text or prompt
(M041), no endpoint (M043), no persistence, no what-if machinery
(M044 orchestrates), no LLM (M040), no frontend (M050); the decision
does not *store* anything and does not call providers or the database.

#### Verification & Notes (added on completion)

- **Human checkpoint:** implemented only after explicit approval
  (decision **D9**, 2026-09-30); the roadmap row now reads
  `P0 🔒 approved (D9)`.
- **Gate:** `scripts/check.ps1` PASSED — 615 passed / 0 skipped (128
  files formatted, ruff clean, mypy clean on 125 sources). New
  coverage: `tests/engines/test_decision.py` = 21 tests (five engines
  now total 126). Bandit 0, pip-audit clean (no new deps).
- **Files:** created `src/engines/decision.py`,
  `tests/engines/test_decision.py`; modified `src/engines/__init__.py`
  (6 exports + docstring "five engines"). No DB, no endpoint.
- **Findings:**
  - **Blind-farm safety came free.** The stance rule never needed its
    own blindness clause: with no signals, M034 already emits
    `soon`-priority data-quality actions, and "any soon → monitor"
    floors the farm at `monitor`. Tested explicitly — the guard that
    M034's spec called a precondition became M039's outcome.
  - **`disease_control` is a new action category**, owned by M039
    (M034's `RECOMMENDATION_CATEGORIES` untouched); `scouting` and
    `monitoring` are reused for verify/monitor. If M041/M050 ever
    switch on categories, this is the one that arrives later than
    M034.
  - Worst-verdict-per-plot collapse means a farm's verdict counts sum
    to *affected plots*, not photos — M041 must phrase "1 plot
    detected", never "1 photo detected".
  - The roadmap's `P0 ??` and 🔒 both resolved at once: D9 records
    approval, and the emoji in the roadmap line doesn't survive a
    cp1252 console (`??`), so edits to that row must be matched from
    file reads, not terminal output — same trap as em dashes.
  - Ordering ties are structurally impossible (priority → origin →
    code → plot name → plot id), which is exactly what M044 needs:
    hypothetical re-runs diff byte-for-byte.
- **Not built (per spec):** no thresholds/evidence re-derivation, no
  advisory text (M041), no endpoint (M043), no persistence, no
  what-if (M044), no LLM, no frontend.

### M040 — LLM provider interface + demo provider (templated)

**Priority:** P0 **Depends On:** M021
**Status:** done

#### Objective
The typed `llm` family contract every model-backed source must satisfy —
`LLMRequest` / `LLMResponse` / `LLMUsage` validated at the boundary, the
abstract `LLMProvider.complete(request)` and the typed
`get_llm_provider()` accessor — plus a deterministic, network-free
**templated** demo registered under `("llm", "demo")` through the normal
M021 registry path.

#### Why This Milestone Exists
M041 turns a `FarmDecision` into a prompt and must get back one
canonical shape of text it can validate and serve; M042 swaps in a live
model behind the same ABC without touching M041; M043 serves that text
and M050 renders it. The family flag (`llm_provider`, M002) and the
`KNOWN_FAMILIES` slot have existed since M021 — this milestone fills
them, exactly as M036 did for `disease`.

#### Files Expected to Be Created
- `src/providers/llm.py` (models, ABC, typed getter)
- `src/providers/llm_demo.py`
- `tests/providers/test_llm.py`

#### Files Expected to Be Modified
- `src/providers/__init__.py` (contract exports + one registration import)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None. No table, no endpoint, no persistence — advisory text is stored
only by a milestone that asks for it (none does yet).

#### API Changes
None. The provider is consumed by M041's service and exposed by M043.

#### External Dependencies
None (pydantic + stdlib). Deliberately **no** HTTP client here: M042's
live provider owns its own pooled `httpx.AsyncClient`, the way M024 did.

#### Design Decisions
- **One round-trip, no streaming, no chat history.** `complete(request)`
  → `LLMResponse`: M041 asks one question and gets one answer.
  Streaming or multi-turn messages can arrive as optional fields later
  without breaking this contract; nothing in M041–M043 needs them.
- **`system` = instructions, `prompt` = content.** The split is what
  makes the demo honest: the demo renders **only `prompt`** (the facts
  a farmer should read) and drops `system` (the instructions to the
  model). A templated demo must never quote instructions back as advice,
  so M041 puts every fact it wants displayed into `prompt`.
- **The demo is a fixed template, not a model:** a seeded opening line
  plus the caller's `prompt`, word-truncated to the caller's own budget.
  It cannot invent agronomic claims — the request is its only source of
  facts.
- **Budget = `max_tokens × CHARS_PER_TOKEN (4)`.** `max_tokens` bounds
  the demo's output the way it bounds a live model's, through a
  documented 4-chars-per-token heuristic; truncation at a word boundary
  yields `finish_reason="length"`, otherwise `"stop"`.
- **Determinism from the request itself** (`request_seed`: sha256 of
  system + prompt + max_tokens + temperature) — the same request gives
  byte-identical text, and temperature only picks *which* fixed opening
  is used (a template has no other use for it). Documented behavior:
  opening drawn from a 3-line vocabulary; `prompt` echoed verbatim when
  it fits the budget.
- **Usage is an estimate in demo mode** (`ceil(chars / 4)` per side,
  `total = prompt + completion`); M042 maps whatever its upstream
  reports. No sum invariant on the model, so a live provider is never
  forced to contradict its upstream's numbers.
- **Bounds are validated at construction:** `prompt` 1–16 000 chars and
  not blank, `system` ≤ 4 000, `max_tokens` 1–8192 (default 2048),
  `temperature` 0–1 (default 0.2), `text` 1–65 536, usage ≥ 0,
  `finish_reason ∈ {stop, length}`. A live provider parsing an upstream
  payload into these models gets a `ValidationError`, which **it** maps
  to `ProviderResponseInvalid` at its boundary (M036 rule).
- **No `ValueError` at request time** — a bad request is a
  `ValidationError` from the pydantic model (caller bug, caught before
  any upstream is contacted). M036's empty-payload `ValueError` exists
  only because bytes carry no model; here the request *is* a model.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/providers/llm.py`: models, ABC, getter.
3. `src/providers/llm_demo.py`: `@register` demo provider.
4. `src/providers/__init__.py`: exports + registration import.
5. `tests/providers/test_llm.py`.
6. Gate, bandit, pip-audit, docs, state, two commits.

#### Testing Criteria
`tests/providers/test_llm.py` (pure unit — no DB, no network):
- [x] registered through the normal settings path: `get_provider("llm")`
  resolves the demo (default flag), typed getter returns `LLMProvider`,
  family/mode/name correct, registry caches one instance;
  `get_llm_provider(mode="live")` → `ProviderNotRegistered` (M042 not
  built).
- [x] determinism: identical request → identical text/usage/
  finish_reason; different `prompt` → different text; `request_seed`
  differs when only `temperature` changes.
- [x] templating: `system` never appears in the output; `prompt` quoted
  verbatim when it fits the budget; opening comes from `OPENINGS`.
- [x] budget: small `max_tokens` → word-boundary truncation,
  `finish_reason == "length"`, output shorter than the prompt; large →
  `"stop"`.
- [x] usage: non-negative ints, `total == prompt + completion`, estimates
  match `ceil(chars / 4)`.
- [x] contract validation: blank prompt, over-long prompt/system/text,
  `max_tokens` and `temperature` out of range, negative usage, unknown
  `finish_reason` → `ValidationError`.
- [x] sweep: ≥ 60 distinct requests → every output within the documented
  shape (non-empty text, `source ==` demo name, at least two different
  openings, at least one truncation, at least one `"stop"`).

#### Verification Commands
```bash
uv run pytest tests/providers/test_llm.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No live model, no HTTP call, no API key handling (M042, 🔒); no prompt
construction from `FarmDecision`, no advisory phrasing, no output
validation policy (M041); no endpoint (M043), no persistence, no
streaming, no stored token accounting.

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED with live dev DB (65432) — ruff
  format OK (130 files), ruff check OK, mypy OK (128 sources), pytest
  **639 passed / 0 skipped** (+24 new `test_llm.py`). Bandit `-r -ll`
  on `src` + `workers` = 0 findings; pip-audit clean. **No new
  dependencies** — pydantic + stdlib only, so D8's pin/audit/record
  checklist had nothing to record.
- **Files:** created `src/providers/llm.py`,
  `src/providers/llm_demo.py`, `tests/providers/test_llm.py`; modified
  `src/providers/__init__.py` (contract exports, one registration
  import, `__all__`) and `MILESTONES.md`.
- **Findings:**
  - `llm` was the last `KNOWN_FAMILIES` slot with no contract behind it
    — and it needed **zero config work**: the `llm_provider` flag has
    existed since M002 and `.env.example` already documents
    `LLM_PROVIDER=demo`. Reserving slots early (M021/M002) again paid
    for itself, exactly as M036 noted for `disease`.
  - **The `system`/`prompt` split is the honesty seam.** The demo has
    no model, so it renders `prompt` and drops `system`: M041 must put
    every farmer-visible fact in `prompt` and keep instructions in
    `system`, otherwise a demo run would quote the prompt *instructions*
    back as advice. Contract rule, not a preference — tested.
  - **No `total == prompt + completion` invariant on `LLMUsage`.** A
    live upstream (M042) is never forced to contradict its own numbers;
    the demo computes the sum itself.
  - Word-boundary truncation needed a **double fallback**: `rfind(" ")`
    over a tiny budget returns `0`/`-1`, and slicing the leading spaces
    of a prompt can produce an empty body — fall back to the raw
    prefix, then to the header alone (`LLMResponse.text` stays ≥ 1 char
    because the opening line always renders).
  - `max_tokens` default 2048 → an 8192-char demo budget. M041's prompt
    must fit that budget or accept `finish_reason="length"` truncation
    in demo mode (the flag is reported, never silent).
  - The demo is seeded **from the request** (`system` + `prompt` +
    `max_tokens` + `temperature`), so `temperature` only rotates three
    fixed openings — documented, tested (`request_seed` differs per
    field), and deliberately unable to vary the *content*.
- **Not built (per spec):** no live model or key handling (M042, 🔒),
  no prompt construction from `FarmDecision` / advisory phrasing (M041),
  no endpoint (M043), no persistence, no streaming.

### M041 — AI advisory generation service (decision → prompt → validated text)

**Priority:** P0 **Depends On:** M039, M040
**Status:** done

#### Objective
`src/ai/advisory.py` — `generate_advisory(decision, *, provider=None)`
→ `Advisory`. It renders a `FarmDecision` (M039) deterministically into
an `LLMRequest` (instructions in `system`, farmer-visible facts in
`prompt`, per M040's contract rule), calls the LLM provider, validates
the returned text, and attaches the **data-gap caveats M041 owns and no
model may omit**. `build_request(decision)` and `advisory_caveats(decision)`
are pure and separately testable.

#### Why This Milestone Exists
M043 must serve *one* answer and M050 render *one* verdict, both with
the honesty guarantees already applied — not re-derived per endpoint.
M044 re-runs the pipeline hypothetically, so advisory generation has to
be a callable step in that re-run, not something embedded in a route.

#### Files Expected to Be Created
- `src/ai/advisory.py`
- `tests/ai/__init__.py`
- `tests/ai/test_advisory.py`

#### Files Expected to Be Modified
- `src/ai/__init__.py` (exports + package docstring — the package has
  been an empty reserved slot since M001)
- `MILESTONES.md`, `ENGINEERING_STATE.md`

#### Database Changes
None. No table, no endpoint, no persistence — an advisory is computed
on demand (M043 exposes it).

#### API Changes
None (M043 exposes it).

#### External Dependencies
None new — pydantic + the existing engine/provider modules.

#### Design Decisions
- **Package boundary:** `src/ai/` owns decision → text (prompt
  construction, the provider call, output validation). `src/services/`
  stays DB/state I/O, `src/engines/` stays pure rules over handed-in
  data. `build_request` is pure; only `generate_advisory` does I/O.
- **`Advisory`** = `farm_id`, `stance`, `text`, `caveats`, `source`,
  `finish_reason`, `generated_at`, plus a `rendered` property joining
  `text` and the caveats with blank lines. `generated_at` is the
  *provider's* timestamp — M041 reads no clock itself.
- **Facts are copied, never re-derived.** Action `title`/`detail` land
  in the prompt verbatim (M032/M033/M039 evidence-reuse rule), in the
  decision's own total order, prefixed with priority; risk score/band,
  health level, stance, plot count and the four disease verdict counts
  are echoed as-is.
- **The prompt is bounded:** at most `PROMPT_ACTION_LIMIT = 15` actions
  are listed, the remainder summarised as `... and N more actions not
  shown` — a farm with 100 actions still builds a request inside
  `PROMPT_MAX_CHARS` and inside the demo's `max_tokens × 4` budget, so
  demo mode never truncates a real advisory.
- **Data gaps are handled twice, on purpose:** already present in the
  facts as M034's `soon` data-quality actions (the model sees the
  blindness as work to do), and *guaranteed* by M041's own `caveats`
  list appended outside the model's control. The prompt carries no
  separate "data gaps" section, so the demo (which echoes `prompt`) does
  not print the same sentence twice.
- **Caveats are M041-owned:** stale signal families and the count of
  plots with unknown health factors, worded once here. A model may
  repeat them; it can never drop them (M034's rule: explain the
  blindness rather than quoting `healthy`).
- **Output validation reuses the provider taxonomy.** Blank-after-strip
  text, text over `ADVISORY_MAX_CHARS` (4 000), or output containing
  the system instruction verbatim (the model echoed instructions as
  advice — the exact failure M040's demo prevents structurally) all
  raise `ProviderResponseInvalid`, so M043 has **one** error path for
  "upstream gave us something unusable". `ProviderError` subclasses from
  the provider propagate untouched.
- **Provider is injectable** (`provider=` keyword) and defaults to
  `get_llm_provider()` — settings-driven through the normal M021 path.
- **No caller-bug guards needed:** `FarmDecision` is already a
  validated pydantic model with M039's own guards upstream.

#### Implementation Steps
1. Spec (here), roadmap → in-progress.
2. `src/ai/advisory.py`: constants, `Advisory`, `build_request`,
   `advisory_caveats`, `generate_advisory`.
3. `src/ai/__init__.py`: exports + package docstring.
4. `tests/ai/test_advisory.py`.
5. Gate, bandit, pip-audit, docs, state, two commits.

#### Testing Criteria
`tests/ai/test_advisory.py` (pure unit — no DB, no network):
- [x] `build_request` is deterministic (same decision → identical
  request) and honours the M040 split: `system` holds instructions and
  never any fact; `prompt` holds facts and never the instruction text.
- [x] facts verbatim: every shown action's `title` and `detail`
  appear in the prompt; stance, health level, risk score/band, plot
  count and all four verdict counts appear; > 15 actions → the
  `... and N more actions not shown` line.
- [x] prompt bounds: a 100-action decision still fits
  `PROMPT_MAX_CHARS`; `system` fits `SYSTEM_MAX_CHARS` and the prompt
  fits the demo's `max_tokens × 4` budget.
- [x] caveats: clean decision → none; stale families → one naming each
  family; unknown-factor plots → one with the count (singular/plural
  worded correctly); both → two in a stable order; `rendered` joins
  text and caveats.
- [x] end-to-end through the default (demo) provider: non-empty text
  built from the request, `source`/`finish_reason`/`generated_at`
  passed through, `farm_id`/`stance` echoed.
- [x] validation: whitespace-only text → `ProviderResponseInvalid`;
  over-length text → same; text containing the system instruction →
  same (a fully empty response cannot reach M041 — `LLMResponse.text`
  is `min_length=1` from M040).
- [x] a stub raising `ProviderUnavailable` propagates unchanged
  (identity asserted).
- [x] no clock read by M041 (`generated_at` equals the stub's fixed
  timestamp).

#### Verification Commands
```bash
uv run pytest tests/ai/test_advisory.py -v
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

#### Definition of Done
Standard checklist (Section 5).

#### What Must NOT Be Implemented Here
No endpoint (M043), no persistence, no prompt *content* beyond what
M039's decision carries (no new agronomic rules — M041 adds no
thresholds), no streaming, no live model or key handling (M042, 🔒),
no what-if machinery (M044), no frontend rendering (M050).

#### Verification & Notes (added on completion)

- **Gate:** `scripts/check.ps1` PASSED with live dev DB (65432) — ruff
  format OK (134 files), ruff check OK, mypy OK (131 sources), pytest
  **656 passed / 0 skipped** (+17 advisory tests). Bandit `-r -ll` on
  `src` + `workers` = 0 findings; pip-audit clean. **No new
  dependencies.**
- **Files:** created `src/ai/advisory.py`, `tests/ai/__init__.py`,
  `tests/ai/test_advisory.py`; modified `src/ai/__init__.py` (first
  content — the package has been an empty reserved slot since M001).
  No DB, no endpoint, no migration.
- **Findings:**
  - **The reserved package paid off.** `src/ai/` needed only a
    docstring and re-exports. The boundary is now written down:
    `src/ai/` = decision → text *with* provider I/O, `src/services/`
    = DB/state I/O, `src/engines/` = pure rules over handed-in data.
  - **Honesty is never delegated.** Caveats (stale families, blind
    plots) are appended by M041 outside the model's control, and the
    same gaps already travel *inside* the facts as M034's
    data-quality actions — so the prompt carries no separate "data
    gaps" section. Adding one would have made demo mode print the same
    sentence twice (the demo echoes `prompt`).
  - The output policy reuses `ProviderResponseInvalid`, giving M043
    **one** error path for "upstream gave us something unusable":
    blank-after-strip, over `ADVISORY_MAX_CHARS`, or instruction echo.
    `ProviderError` from the provider passes through untouched
    (identity asserted in the test).
  - **A fully empty response can never reach M041** — M040's
    `LLMResponse.text` is `min_length=1`, so the blank-text test had
    to use whitespace-only input. Caught while writing the test; the
    reason is recorded in the checkbox rather than hidden.
  - The prompt is bounded *by construction*: `PROMPT_ACTION_LIMIT=15`
    keeps a 100-action farm at ~1 900 chars — inside
    `PROMPT_MAX_CHARS` (16 000) and inside the demo's
    `max_tokens × 4 = 8 192` budget, so demo mode can never truncate
    an advisory (`finish_reason="length"` on an advisory would be a
    silent truncation of advice).
  - `Advisory.generated_at` is the *provider's* timestamp: M041 reads
    no clock, which is what lets M044 re-run the whole
    decision → advisory step without clock injection.
  - Provider injection (`provider=`) means the validation tests need
    no registry monkeypatch — the M040 keyword exists for exactly
    this.
- **Not built (per spec):** no endpoint (M043), no persistence, no new
  agronomic thresholds, no live model or key handling (M042, 🔒), no
  what-if (M044), no frontend (M050).