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
