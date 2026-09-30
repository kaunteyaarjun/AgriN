# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "(none in progress) — M056 (performance & resource review) is done: MODIS /dates calendar cached process-wide (12 h TTL + asyncio.Lock double-checked read; invalid/error responses never cached; a batch now costs 1 dates + N subset calls instead of 2N); all three ingest_*_for_all loops restructured to one point query + bounded-concurrent fetches (asyncio.Semaphore, settings.ingest_concurrency=4 ge=1) + strictly serial persist — an AsyncSession is never used concurrently, statuses/order/isolation byte-identical; exact query-count regression budgets in new tests/perf (analyze_farm 3, GET /farms 4, GET /farms/{id} 2, GET /farms/{id}/state 5); /ready wait_for cancellation residual (M007 deferral) measured in-process → CLEAN and guarded by a new test holding a real pooled connection; resource-review inventory recorded (no new deps, no schema change). Also flipped the M054/M055 roadmap rows their completion passes left at in-progress. Next per roadmap: M057 (test-fixture consolidation + CI, backend scope). Frontend chain M046-M053 and M042/M058 remain 🔒 locked on human approval."
Completed milestones: ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M008", "M009", "M010", "M011", "M012", "M013", "M014", "M015", "M016", "M017", "M018", "M019", "M020", "M021", "M022", "M023", "M024", "M025", "M026", "M027", "M028", "M029", "M031", "M032", "M033", "M034", "M035", "M036", "M037", "M039", "M040", "M041", "M043", "M044", "M045", "M054", "M055", "M056"]
Current implementation status: "M056 done: performance & resource review. src/providers/satellite_live.py: process-wide MODIS calendar cache (_calendar tuple + asyncio.Lock + CALENDAR_TTL_S 12h, double-checked read inside _calendar_dates; invalid/failed /dates responses raise before the store is written so they are never cached; reset_calendar_cache() + autouse tests/conftest.py fixture — the reset also RECREATES the lock so per-test event loops never inherit a loop-bound primitive). src/ingestion/{satellite,weather,soil}.py: ingest_*_for_all = one point query ordered by farm id (was N per-farm centroid queries) → asyncio.Semaphore(ingest_concurrency)-bounded concurrent provider fetches via gather → strictly serial persist through the extracted _persist_reading helper; per-farm ingest_*_for_farm entry points unchanged (NotFound + status contracts). Failure taxonomy preserved: ProviderError→provider_error inside the fetch phase, unexpected→failed with rollback in the persist phase, no-geo farms never reach the provider. Settings: ingest_concurrency=4 (Field ge=1), documented in .env.example. New tests/perf/test_query_budgets.py: before_cursor_execute statement recorder with EXACT budgets (analyze_farm 3, GET /api/v1/farms 4, GET /farms/{id} 2, GET /farms/{id}/state 5; zero headroom — M019's ==3 precedent). tests/api/test_health.py: cancellation-residual probe hangs INSIDE a real engine.connect() checkout, lets wait_for expire, asserts pool.checkedout() back to baseline — CLEAN, no health.py change needed. tests/ingestion/test_batch_concurrency.py (4: overlap hits the bound exactly, concurrency=1 sequential, settings default applied when no kwarg, weather/soil wiring smoke). tests/providers/test_satellite_live.py +6 calendar-cache tests (one dates per batch, cross-instance sharing, TTL-0 refetch, concurrent single-flight, failures/invalid never cached). tests/core/test_config.py +1 (default 4, 0 rejected). Total 16 new tests → 754 passing. Also corrected: M054/M055 roadmap rows still said in-progress."
Known bugs: []
Known security issues:
  - "M055 closed: login/refresh rate limiting (was open since M009), refresh-token revocation/logout, error-shape unification. Remaining by design: stateless access tokens keep working up to 15 min after logout-all (documented — no access-token denylist), rate limiter is per-process (limit × workers when multi-worker), /docs defaults to ON (DOCS_ENABLED=false for prod — SECURITY.md owns the write-up in M059)."
Known performance issues:
  - "M056 mitigated: live satellite's per-farm cost no longer includes the /dates call (cached 12 h process-wide — batch = 1 dates + N subset instead of 2N; the remaining ~3 s/farm subset call is upstream-bound), and batch loops overlap fetches (bound: ingest_concurrency=4). Live weather stays ~1 call/farm. Read paths are pinned by exact query budgets (M056) plus M019's 3-query contract; no further known hot spots."
Known resource/memory issues:
  - "M056 RESOLVED the /ready asyncio.wait_for cancellation residual (M007 deferral): measured in-process with a REAL checked-out connection (sleep inside async with engine.connect(), 2 s budget) — pool.checkedout() returns to baseline every run; guarded by test_ready_timeout_with_real_checked_out_connection_returns_it. Resource inventory: httpx clients pooled + aclose'd (M024/M027), dispose_engine() in every worker, rate-limiter keys bounded (M055), upload byte/pixel caps (M035). Deferred with owners: orphaned upload bytes (M035), per-process rate limiter (M055 multi-worker note)."
Technical debt:
  - "Autogenerate migrations must ALWAYS be hand-reviewed — M008 caught a duplicated same-name CHECK constraint in the generated output."
  - "Error-shape debt PAID in M055: every client error now answers {error_code, message} (pydantic 422, Starlette 404/405, AppError). Remaining known debt: passlib 1.7.4 is unmaintained (bcrypt pinned 4.0.1 to keep it working) — dropping passlib is future work; orphaned upload bytes on plot delete (M035, cleanup deferred)."
Blocked tasks:
  - "P1 milestones M051-M053 are dependency-blocked: M051 (what-if UI) needs M050 (M045 done), M052/M053 need M046. M038 (disease live model) waits on a live-model decision. P0s remaining: M046-M050 (frontend chain, 🔒 human checkpoint first) and M057 (test/CI consolidation — the only unblocked backend P0). M054-M056 now done."
Next milestone: "M057 (regression suite consolidation + CI script, P0, deps met): consolidate the duplicated test helpers (_db_reachable/_alembic_config/_db/_client/_headers/_users fixtures across ~12 API test files, plus tests/perf and tests/ingestion copies) into conftest fixtures — 754 tests must stay 754 (moves, not deletions) — and add .github/workflows/ci.yml running the six gate steps against a postgis/postgis:16-3.4 service on 65432. After M057 the backend roadmap stops: M058 (docker-compose) needs its scope approved and the frontend chain M046-M053 / M042 remain locked on human approval."
Last verification: "M056 gate PASSED (six-step: format → lint → mypy → pytest → bandit → pip-audit) with live dev DB (65432): ruff format OK, ruff check OK, mypy OK, pytest 754 passed / 0 skipped (16 new), bandit -r -ll on src + workers = 0 findings, pip-audit clean (no new dependencies). DB checked for seed residue before the run (0 @agrin.demo users). Gate ran BEFORE the commits (M044 rule)."
Last test result: "pytest = 754 passed (demo-seed 8, ratelimit 8, errors-API 5, hardening-API 5, auth-API 21, whatif-API 11, test_whatif 26, analysis 7, advisory-API 5, advisory 17, llm 24, decision 21, disease-engine 18, engines-health 38, recommend 22, risk 27, disease-provider 12, images-API 10, normalize 64, weather-live 57, satellite-live 46, soil 15, providers 15, state 14, weather-demo 14, satellite 14, farm-state-api 14, idor 13, plots-API 13, farms-API 15, farmers-API 15, soil-ingestion 11, satellite-ingestion 11, weather-ingestion 10, batch-concurrency 4, query-budgets 4, farm-state-service 10, health 10, rbac 11, root 4, config 9, db 4, redact 3, errors 8, logging 4, security 17, user 6, farm-model 11, farmer-model 8, plot-model 11, migrations 2, smoke 2)"
```

## Checkpoint decisions (human-confirmed, 2026-09-26)

| # | Decision |
|---|---|
| D1 | Section 3 locked architecture — confirmed as-is |
| D2 | Dev commands → `uv run ruff|mypy|pytest` + `scripts/check.ps1` (no make/just on this Windows host) |
| D3 | Password hashing → `passlib[bcrypt]` + pin `bcrypt==4.0.1` — **revisited in M055: keep both** (passlib 1.7.4 breaks on bcrypt ≥ 4.1, removed `__about__`; passlib unmaintained → dropping it is recorded future work). Work factor stays passlib's bcrypt default (12 rounds). |
| D4 | Authorized system actions: `git init`; start Docker Desktop when M003+ verification needs the dev Postgres |
| D5 | JWT library → **PyJWT** (Section 3 allows "python-jose or pyjwt") |
| D6 | Python → **3.12** pinned via `.python-version` / `requires-python` |
| D7 | Farm geometry → **PostGIS `geometry(Geometry, 4326)` column** (human-confirmed 2026-09-27; rejected GeoJSON-in-JSONB and plain lat/lng point). DB image becomes `postgis/postgis:16-3.4`, new pinned dep `geoalchemy2`. |
| D8 | `httpx` **promoted from dev-only to runtime** dependencies at the same pin `0.28.1` (human-confirmed 2026-09-28) — live providers (M024+) need it at runtime; dev extra unchanged otherwise. |
| D9 | **M039 human checkpoint approved** (human-confirmed 2026-09-30) — the 🔒 structured-decision engine may be implemented; all code deps (M033, M034, M037) were already met when approval was granted. |

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
| M015 | `750fc19` |
| M016 | `d10854d` |
| M017 | `34622b4` |
| M018 | `b0cc7c5` |
| M019 | `293101c` |
| M020 | `eef7aa6` |
| M021 | `890755e` |
| M022 | `90ea7ce` |
| M023 | `31d3988` |
| M024 | `3ee8e5d` |
| M025 | `15d5f73` |
| M026 | `33625fe` |
| M027 | `e44de02` |
| M028 | `8913402` |
| M029 | `05fce19` |
| M031 | `496eae9` |
| M032 | `3acd7f9` |
| M033 | `9a494b9` |
| M034 | `66b26a2` |
| M035 | `998d2eb` |
| M036 | `980298e` |
| M037 | `e15b3f8` |
| M039 | `35bd565` |
| M040 | `f38f448` |
| M041 | `ac6ddda` |
| M043 | `17eeb78` |
| M044 | `54c1180` (engine), `82e4c1a` (tests), `c34c874` (fix) — all pushed with message `commit` |
| M045 | `3a0412f` |
| M054 | `c23b814` |
| M055 | `258fcf9` |

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
- 2026-09-28 (M017): This host has **two** `Temp\opencode` directories
  (`C:\Users\91797\...` and `C:\Personal\91797\...`); files written via
  the file tool landed in the latter. When running a temp script, use
  the exact path reported at write time, not `$env:TEMP\opencode`.
- 2026-09-28 (M017): `live_m017.py` + the audit live checks run against
  a real `uvicorn src.main:app --port 8000` child process — kill it by
  the PID from `netstat -ano | Select-String ":8000.*LISTENING"` (M009
  lesson) before re-running tests.
- 2026-09-28 (M019): **Partial-seed failures must stay tracked.** A test
  helper that inserts the user row before later steps can raise must
  append the id to the cleanup list *inside the helper, right after its
  commit* — the old pattern (caller appends after the helper returns)
  leaked 9 seed sets when the helper crashed mid-way, breaking 4
  unrelated tests in the next gate (`MultipleResultsFound` in
  `test_plot`'s unscoped name lookup, wrong privileged-list `total`
  counts). `_seed` in `tests/services/test_farm_state.py` now owns
  tracking; also hardened `tests/models/test_plot.py` to scope its
  `Block A` reads by `farm_id`. The gate's migration round-trip wiped
  the residue automatically.
- 2026-09-28 (M021): **ruff 0.16.9 formats Markdown code blocks** —
  `scripts/check.ps1` runs `ruff format --check .`, which covers
  `MILESTONES.md`'s fenced Python blocks. Aligned trailing comments
  inside a spec's code block fail the gate; run `uv run ruff format .`
  after appending specs (discovered when the gate failed despite
  231 passed).
- 2026-09-28 (M021): lock honored — M021 design was presented for
  human approval FIRST (approved as written), roadmap flipped to
  in-progress only after sign-off, then implemented. Next locked
  milestone: M042 (LLM live provider); M039/M046/M058 also 🔒.
- 2026-09-28 (M023): **House rule: every DB-touching test must request
  the `_db` fixture, even without seeded users.** A test that opens a
  session without `_db` leaves a pooled connection bound to its
  torn-down event loop; the *next* test's reachability probe then
  fails with a misleading "dev Postgres not reachable" skip (reproduced
  via `-k` pair bisection before the fix — `test_unknown_farm_…`
  skipped its successor `test_ingest_for_all_…` but passed alone).
  `_db`'s teardown (`dispose_engine`) is what clears the pool.
- 2026-09-29 (M024): **first real network provider shipped.** Recipe
  that later live providers (M027/M030/M040) should copy: own one
  pooled `httpx.AsyncClient` (module-constant timeout) with an
  injectable client/base_url for `MockTransport` tests, map every
  transport/HTTP/parse failure onto the M021 taxonomy inside `fetch`
  (no raw exception may escape), override `aclose()`, register with
  one comment-marked import line, keep the settings default on
  `demo`. `httpx.MockTransport` propagates handler exceptions
  unchanged, so taxonomy tests run through the genuine client path.
- 2026-09-29 (M024): **absent ≠ unknown.** `condition=None` when the
  upstream omits `weather_code`, `cloudy` when it sends a value we
  can't fold — an optional field must not be filled with a plausible
  guess. Same idea applies to every future live mapping.
- 2026-09-29 (M024): Docker Desktop was not running at gate time; the
  authorized path (D4) is to start it and `docker compose up -d db`
  (port 65432) before any gate run — DB-touching tests skip without
  it, and a "green" run with skips is NOT a passing gate.
- 2026-09-29 (M027): **keyless-source research is now a repeatable
  step.** Before spec'ing any live provider, screen sources on three
  gates in order: (1) can it be used *without credentials we cannot
  mint autonomously* (no account, no key — `Settings` has no key
  fields), (2) does it return machine-readable data for a *point*
  (not tiles/rasters that need a new heavy dep), (3) is it documented
  and reachable from this host. Sentinel/Copernicus/Earth Engine
  failed (1); Planetary Computer/Earth Search failed (2); ORNL DAAC
  passed all three. Put the rejected alternatives + the reason in the
  spec so the next reader doesn't redo the search.
- 2026-09-29 (M027): **`/dates` is the global MODIS calendar**, not a
  per-point availability list — a mid-ocean point returns the same
  610 entries. Only `/subset` proves coverage (it answers `subset: []`
  over water → `ProviderResponseInvalid`, deliberately not a null
  reading: a fake observation is worse than a recorded provider
  error).
- 2026-09-29 (M027): **upstream cost scales with how much you ask
  for** — 3 composites took 11.5 s, 1 composite ~3 s (hence
  two requests beat one wide window), and NASA's latency at Nairobi
  measured **47 days** (a fixed look-back window would eventually
  request nothing and fail). Also: ORNL answers 4xx with **plain
  text**, not JSON — surface it trimmed (`UPSTREAM_MESSAGE_MAX`), never
  as a raw dump.
- 2026-09-29 (M027): **date-sensitive provider tests must derive their
  fixtures from `datetime.now(UTC).date()` at import time**
  (`PAST_DAY`/`LATEST_DAY`/`FUTURE_DAY`), never hardcode calendar
  strings — otherwise "newest composite ≤ today" tests rot the moment
  the calendar advances.
- 2026-09-29 (M024+M027): **P1 pass complete.** Both unblocked P1s
  shipped; M038/M051/M052/M053 are blocked on unstarted P0 specs
  (M036/M037, M043/M045/M046/M050) and M030 (soil live) is P2 — the
  next milestone needs a human decision (see `Next milestone`).
- 2026-09-29 (M031): **the cache field name is not the truth about the
  value.** `rainfall_mm_24h` means a 24 h accumulation to the demo
  provider but the *current hour* to Open-Meteo, and MODIS's NDVI is a
  16-day composite while the demo's is a single overpass. Store raw
  (per M019), then normalize through a per-source profile; never
  convert (or compare) a payload whose window you don't know. The same
  rule applies to any new provider: **adding a source means adding its
  `SOURCE_PROFILES` entry**, and until you do, its timeframe-derived
  fields stay `None`.
- 2026-09-29 (M031): **physical range ≠ agronomic threshold.** The
  bounds in `normalize.py` (temp −90..60 °C, pH 0..14, NDVI −1..1 …)
  only say "this number cannot be real"; out-of-range becomes `None`
  because an impossible value is not data. Decision thresholds
  ("NDVI < 0.4 = stress", "pH < 5.5 = too acidic") belong to M032/M033/
  M034 — do not move them into this layer, or the engines lose the
  right to disagree with each other.
- 2026-09-29 (M031): **`bool` must be excluded before `int | float`.**
  In Python `True` is an `int`, so a truthy flag landing in the signals
  doc would otherwise normalize as `1.0`. `_number` checks
  `isinstance(value, bool)` first, then `math.isfinite` — copy that
  order into any future JSONB numeric reader.
- 2026-09-29 (M031): **no staleness policy lives here.** `age_seconds`
  is computed (and may be negative for a future `observed_at`); the
  *threshold* at which a signal is "stale" is a per-engine decision
  (M019's standing rule). If two engines disagree about freshness,
  that is a feature of their domains, not a bug to centralize.
- 2026-09-29 (M032): **the staleness thresholds now exist** (they were
  deliberately deferred twice) — `STALE_AFTER_SECONDS` in
  `src/engines/health.py`: weather 24 h, soil 24 h, **satellite 90 d**.
  The 90 is derived from measurement (M027: 47-day NASA latency at
  Nairobi + 16-day composite), not taste; a "clean" 16/30-day number
  would mark every real MODIS reading stale. Any later engine reading
  signals (M033/M034/M047) must reuse these constants rather than
  inventing its own notion of fresh.
- 2026-09-29 (M032): **"healthy" must be gated, not defaulted.** The
  first draft aggregated the worst *non-unknown* factor, which made a
  plot with a registered crop and **zero signals** come out `healthy`
  (only `planting` was `ok`). Caught while writing the test, fixed
  before the spec was closed: planting gates the verdict, and no
  evaluated signal factor → `unknown`. Rule of thumb for every future
  engine: *absence of evidence is never evidence of health.*
- 2026-09-29 (M032): new package boundary — **`src/services` does I/O,
  `src/engines/` does rules.** Engines take assembled state
  (`NormalizedFarmState`) and return pydantic DTOs; no session, no
  provider, no persistence. M033/M034/M039 should land in
  `src/engines/`, and an endpoint (M047/M048) will be the thing that
  calls them.
- 2026-09-29 (M032): **two unknowns, two messages.** `no rainfall
  reading` (provider omitted the field) vs `rainfall window unknown
  for this source` (M031's profile lookup found no window) look the
  same to a level (`unknown`) but mean different fixes; keep the
  detail strings distinct. Same for `no observation time` vs
  `stale (…)` — the former is not reported as a stale family.
- 2026-09-29 (M032): engine tests feed **raw docs through M031's
  normalizer**, so they cover the M031→M032 seam instead of
  hand-building `NormalizedSignals`. Copy that pattern for M033/M034 —
  it fails loudly if either side's contract drifts.
- 2026-09-29 (M033): **risk reuses health's evidence strings, not its
  thresholds.** `RiskItem.detail` is the `HealthFactor.detail` from
  M032 verbatim, so a risk item and the health factor behind it always
  read the same sentence; only the three visibility details are new
  strings. Rule: an engine that maps another engine's output must
  inherit its formatting, never re-derive it.
- 2026-09-29 (M033): **staleness outranks hazard detection when one
  doc carries both.** A weather doc 25 h old yields `stale_signals`
  but its temperature reads `unknown`, so no `heat` item appears —
  the ordering test had to use a stale *satellite* doc to keep heat
  live. Expected, and worth remembering for M047: one stale family can
  hide several hazards at once.
- 2026-09-29 (M033): **visibility alone tops out at 55 → `moderate`.**
  Missing all three families (45) + unregistered plot (10) never
  reaches the `high` band (60); you also need at least one real stress
  (30). Deliberate: blindness is a problem, but a *measured* hazard is
  worse.
- 2026-09-29 (M033): helpers `_profile_for`/`_label_for` were promoted
  to public `crop_profile_for`/`crop_label_for` and exported from
  `src/engines` — M034 and M039 need the same profile lookup, so keep
  them importable rather than reaching into another module's privates.
- 2026-09-29 (M034): **signals are farm-level, so plot contrast can
  only come from crop profiles.** Every test that needed "one plot
  healthy, one in trouble" had to differ by crop (maize irrigates at
  32 % moisture, wheat does not), not by soil doc — per-plot variation
  exists only via crop profile + planting date. Recorded as the
  standing limitation until plot-level signal attribution exists.
- 2026-09-29 (M034): **health and advice can disagree by design.**
  With one stale family, M032's rollup may still read `healthy` (three
  known factors evaluated, one unknown) while M034 refuses
  `continue_as_planned` because a factor is unknown. The recommendation
  is the stricter — and correct — one for a farmer; M041 must explain
  the blindness rather than quoting `healthy`.
- 2026-09-29 (M034): the three engines now share one input shape
  (`state`, `health`, `now`) and one evidence source (M032's factor
  detail). M039 should compose them exactly that way — if a fourth
  engine ever needs a different input, that is the smell that the
  contract drifted.
- 2026-09-29 (M034): roadmap "Depends On" cells predate the specs.
  M034's row said `M031` but the engine reads `CropProfile` (M032);
  corrected to `M031, M032` with the deviation recorded in the spec.
  Check the row, not just the prose, when a just-in-time spec reveals
  a dependency.
- 2026-09-29 (M035): **two runtime dependencies were added**
  (`python-multipart==0.0.32`, `pillow==12.3.0`) — D8's discipline
  applies: pinned exactly, `pip-audit` clean, stated here. If a future
  milestone needs another dep, that is the checklist: pin, audit,
  record.
- 2026-09-29 (M035): the default-deny inventory test crashed with
  `KeyError: 'image_id'` before it could even assert 401 — a new
  route had appeared that its `_bind` helper didn't know. Fixed by
  binding every `{param}` generically with a regex, so the *next*
  endpoint can't slip past the sweep. Regression guards compound:
  each new one needs maintenance exactly once, permanently.
- 2026-09-29 (M035): **a truncated file fails with bare `OSError`,
  not `UnidentifiedImageError`.** A JPEG cut in half raises inside
  `Image.open` itself; catching only the documented exception
  yields a 500. `_decode` now maps header-level `OSError` → 422
  `invalid_image`. Pillow's error taxonomy is not something to
  trust by memory — the test caught it in the first run.
- 2026-09-29 (M035): authz-before-bytes is structural, not
  incidental: the inventory test POSTs JSON `{}` at the multipart
  route and still gets 401, because FastAPI solves security
  dependencies before body validation. Worth remembering when
  someone proposes "validate the file first, then check the user".
- 2026-09-29 (M035): plot deletion cascades image *rows* but leaves
  bytes on disk in `var/uploads` (orphaned files — documented,
  cleanup deferred). Any future delete endpoint must remove both
  halves transactionally, or the limitation merely grows.
- 2026-09-29 (M036): **vocabulary belongs to the interface, not the
  engine.** `DISEASE_CATALOG` (code → label + plausible crops) sits in
  `src/providers/disease.py` because it defines what a provider may
  *report*; M037 will read it for its crop blend and M049 for labels.
  If assessment ever needs a disease the catalog lacks, add it here —
  a second list in the engine is how vocabularies fork.
- 2026-09-29 (M036): catalog validation is a pydantic
  `field_validator`, so an unknown code raises `ValidationError` at
  *construction* — the demo cannot drift, and M038's live provider
  must catch and map it to `ProviderResponseInvalid` at its boundary.
  Contract errors that fail at model build time never reach a caller.
- 2026-09-29 (M036): the `"disease"` family was reserved since M002
  (settings flag) and M021 (`KNOWN_FAMILIES`); filling it needed zero
  config changes. Reserving slots early costs nothing and removes a
  whole class of "plumbing" work from later milestones — same trick
  will pay off for `llm` in M040.
- 2026-09-29 (M037): **the blend's one invariant is "discount, never
  boost."** Farm context can disagree with the model (crop mismatch,
  healthy canopy) but must not raise a weak score — a boosting blend
  would let 0.45 × optimism become `detected`. Made testable as
  `effective ≤ raw` across a sweep; M044 (what-if) reuses this engine,
  so the invariant must survive hypothetical re-runs too.
- 2026-09-29 (M037): stress is *consistent* with disease but is not
  *evidence* of it — so `stressed`/`watch` add no multiplier in
  either direction, while `healthy` gets the single ×0.9 discount.
  The asymmetry (bad canopy can't confirm, good canopy can doubt) is
  deliberate; document it before anyone "balances" it later.
- 2026-09-29 (M037): verdict thresholds (0.70 / 0.50) are engine
  constants exported by name (`DETECTED_MIN`, `SUSPECTED_MIN`) —
  M049 must render verdicts from `DISEASE_VERDICTS`, never re-code
  the numbers in the frontend.
- 2026-09-29 (M037): first milestone where the roadmap chain hits a
  🔒 checkpoint *with all code dependencies met* — M039 now waits
  purely on human approval, not on other work. Alternates while
  waiting: M040 (LLM demo), M054 (demo seed).
- 2026-09-30 (M039): **the D9 checkpoint happened exactly as the
  protocol demands** — implementation started only after explicit
  human approval, recorded in the decisions table and the roadmap
  row (`P0 🔒 approved (D9)`). The remaining locks (M042, M046,
  M058) get the same treatment.
- 2026-09-30 (M039): the stance rule needed **no blindness clause of
  its own** — M034's data-quality actions are `soon` by construction,
  so "any soon → monitor" floors blind farms automatically. When one
  milestone's precondition (M034: never reassure the blind) becomes
  another's safety property (M039: never claim routine), that's the
  composition working; don't duplicate the guard.
- 2026-09-30 (M039): `disease_control` is the one action category
  born after M034 — M041/M050 must not assume categories are a
  closed set. Verdict counts are **per plot, not per photo** (worst
  verdict wins); advisory copy says "1 plot detected".
- 2026-09-30 (M039): console emoji trap again — the roadmap's 🔒 in
  the M039 row renders as `??` through cp1252, so a `Select-String`
  round-trip through the terminal lies about the file's contents.
  Edit-match against a direct read (or `ascii()`/`repr()`) whenever
  emoji or em dashes are in play; this is the third occurrence
  (MILESTONES em dashes, `→`, now `🔒`).
- 2026-09-30 (M040): **the `system`/`prompt` split is a contract rule,
  not a preference.** The demo has no model, so it renders `prompt` and
  drops `system`; M041 must put every farmer-visible fact in `prompt`
  and keep instructions in `system`, or demo runs will quote the prompt
  *instructions* back as advice. Tested (`SYSTEM not in text`), stated
  in the spec, and carried here as guidance for M041's prompt builder.
- 2026-09-30 (M040): `llm` was the last `KNOWN_FAMILIES` slot with no
  contract — and filling it needed **zero config work** (`llm_provider`
  flag since M002, `LLM_PROVIDER=demo` already in `.env.example`).
  Second confirmation of the early-reservation trick M036 recorded for
  `disease`: reserve the slot when the pattern lands, not when the
  family is built.
- 2026-09-30 (M040): Docker Desktop was not running at session start;
  the D4-authorized path (start it, `docker compose up -d db`, port
  65432) restored the gate to **639 passed / 0 skipped**. Repeats the
  M024 rule: a "green" run with skips is not a passing gate.
- 2026-09-30 (M040): word-boundary truncation needs a **double
  fallback** — `rfind(" ")` over a tiny budget returns `0`/`-1`, and
  slicing a prompt's leading whitespace can yield an empty body. Fall
  back to the raw prefix, then to the header alone. Any future
  "trim to budget" helper should copy both rungs.
- 2026-09-30 (M041): **the reserved `src/ai/` package finally opened
  for business** (empty since M001). Boundary now written down:
  `src/ai/` = decision → text *with* provider I/O, `src/services/` =
  DB/state I/O, `src/engines/` = pure rules. Reserve the directory
  when the skeleton lands; filling it later costs a docstring.
- 2026-09-30 (M041): **honesty is never delegated.** Data gaps travel
  twice — as M034's data-quality actions inside the prompt facts, and
  as `Advisory.caveats`, appended by M041 outside the model's control.
  Deliberately *no* separate "data gaps" section in the prompt: the
  demo echoes `prompt`, so one would have printed the same sentence
  twice in demo mode.
- 2026-09-30 (M041): a fully empty model response **cannot** reach
  M041 — M040's `LLMResponse.text` is `min_length=1`, so the
  whitespace-only case is the only blank M041 has to strip-and-reject.
  Two boundaries, one gap, each documented where it is enforced.
- 2026-09-30 (M041): `PROMPT_ACTION_LIMIT=15` is not cosmetic — it is
  what keeps demo mode from **silently truncating advice** (the demo
  budget is `max_tokens × 4 = 8 192` chars). A `finish_reason="length"`
  on an advisory would be advice cut mid-sentence; the prompt bound
  test asserts the budget directly so a future cap change fails loudly.
- 2026-09-30 (M041): `ProviderResponseInvalid` was reused for M041's
  own output policy (blank, over-length, instruction echo) instead of
  inventing a second error type — M043 therefore needs exactly one
  upstream-failure mapping, and `ProviderError` from the provider still
  passes through by identity.
- 2026-09-30 (M041): M041 reads no clock (`generated_at` is the
  provider's), so decision → advisory is re-runnable for M044 without
  the clock-injection dance the engines need. Keep that property when
  adding any step to the pipeline.
- 2026-09-30 (M043): **the endpoint came with the pipeline it needed.** Nothing
  assembled the four engines (M039's tests hand-chained them), so M043 introduced
  `run_analysis` (pure, one injected clock) + `analyze_farm` (M019 twin →
  normalize → pipeline). M044's what-if is then *perturb the state, same call* —
  if a future milestone re-chains the engines by hand, this split has failed.
- 2026-09-30 (M043): **`await` at the async boundary.** The route initially called
  M041's async `generate_advisory` without `await`; pure + service tests passed
  while all five route tests failed (pydantic received a coroutine). Only the HTTP
  layer can catch that — cheap evidence that the layer-by-layer test split earns
  its keep.
- 2026-09-30 (M043): one `UpstreamUnavailable` (502, sanitized) now maps **every**
  `ProviderError` — unreachable upstream *and* M041's output-policy rejection. It
  is an `AppError`, so no new handler was needed; the detail is logged, never
  echoed. Keep this the single upstream-failure path when M045 adds a POST route.
- 2026-09-30 (M043): API-test fixtures seed through the **services**, not M020's
  routes — an advisory test must not break when a state endpoint changes. The
  blind-farm path is asserted end-to-end (empty cache → unknown-factor plot →
  `monitor` → non-empty `advisory.caveats` over HTTP), so M041's honesty provably
  survives serialization.
- 2026-09-30 (M044): **gate before push — this milestone broke the rule and the
  gate found two live failures.** The engine/spec/tests were pushed in three
  commits named `commit` (already on `origin/master`, so the messages stay as a
  permanent record), and `scripts/check.ps1` first ran in the *next* session: a
  107-char line in `whatif.py` (format) and `assert (family, field) in
  WHAT_IF_KNOBS` — tuple membership against a *nested* dict is always false, so
  all six knob-sweep params failed while the other 688 tests passed. New house
  rule: **the gate runs before every push, and commits are named
  `M0XX: <objective>` before they leave the machine.**
- 2026-09-30 (M044): **a failing "moves nothing" test can be the fixture's
  fault — and still be a correct failure.** The rainfall sweep used `0.0`
  against a 5 mm/day baseline; both sit below M032's 30 mm/day attention
  threshold, so the knob legitimately moved nothing. Sweeping at `70.0` (above
  the 60 stress threshold) proves the knob. The spec's rule stands: a catalogue
  knob must be able to move an answer at *some* value, and the test must pick
  one.
- 2026-09-30 (M044): **validation is two-phase on purpose.** Range checks run
  against M031's exported bounds *before* normalize (an out-of-range number
  must raise, not degrade to `None` and turn a hypothetical into an unknown
  factor), while the rainfall window check runs *after* (only
  `normalize_signals` knows the source's timeframe). Never merge the phases —
  each exists to stop a different silent corruption.
- 2026-09-30 (M044): **re-stamping is what makes a knob honest.** A hypothetical
  is a statement about *now*, so an overridden family's `observed_at` becomes
  the simulation clock — otherwise M032's staleness gate discards exactly the
  value the user just changed (the classic silent no-op). Proven both
  directions: stale baseline → fresh hypothetical, and the removed staleness
  points show up in `risk_score_delta`. A family the farm never had is
  materialized with `observed_at = now` and **no source**; rainfall on a
  windowless family raises instead of inventing a timeframe.
- 2026-09-30 (M044): M044 added exactly one export batch (`WHAT_IF_KNOBS`,
  `WhatIfChanges`, `WhatIfResult`, `simulate_what_if`). M045 must import from
  `src.engines`, never from `src.engines.whatif` directly (M033's export
  lesson), and derive its request/response limits from `WHAT_IF_KNOBS` rather
  than re-coding them.
- 2026-09-30 (M045): **the gate-before-push rule was applied for the first
  time and the milestone went green on the first run** (11/11 new tests, full
  gate 705 passed). M044's two failures were both pre-push preventable; the
  discipline costs one gate run (~2 min) and buys not pushing broken code.
- 2026-09-30 (M045): **`analyze_farm` reuse was the wrong instinct.** It
  returns a `FarmAnalysis` (running the baseline once for nothing) and would
  have forced a *second* clock read in the route to call the engine. The
  service mirrors it instead: load → normalize → hand to `simulate_what_if`
  with the same `now`. When two services differ only in their final call,
  copy the shell — don't chain the siblings.
- 2026-09-30 (M045): **the dual-422 convention now has one file exercising
  both halves** (`tests/api/test_whatif.py`): pydantic `{detail}` for
  structure (fires before the handler), AppError `{error_code:
  validation_failed}` for the engine's message verbatim. Both are asserted,
  so the M055 unification pass will see exactly what today's clients rely on.
- 2026-09-30 (M045): **M043's completion notes had been left stranded after
  M044's section** (appended at file end while the M044 spec sat before
  them). Moved back under M043's spec while writing M045's. Lesson: append
  completion notes *inside* the milestone's section, not at EOF — the next
  spec lands at EOF immediately after.
- 2026-09-30 (M045): authz-before-body re-confirmed for POST (M035's
  structural lesson): anon gets 401 even when the body is valid, and a
  malformed path id still yields pydantic's 422 — the read matrix does
  not care which verb carries the argument.
- 2026-09-30 (M054): **the CLI deliberately takes no `--password`
  argument** (spec step said "argparse like the ingest workers") — a
  secret on a command line is visible in the process list. The worker
  reads `Settings.demo_password` (env `.env`) and prints the resolved
  credentials once. Deviation recorded in the spec's completion notes;
  when a later milestone wants CLI flags, follow M024's config
  discipline instead of argv.
- 2026-09-30 (M054): **determinism ≠ static timestamps.** uuid5 keys
  make ids/emails byte-stable while `observed_at`/`planted_on` stay
  seed-relative (now−30 min, today−N days) — a fixed absolute date
  would go stale and M032's staleness gate would mark the seeded
  signals dead. Tests pin the clock (`now=NOW`) so assertions are
  exact; the live CLI uses the real clock so demos stay fresh.
- 2026-09-30 (M054): M019's spec reserved `set_plot_state`/
  `put_signals` for this milestone and they plugged in unchanged —
  including their internal commits (seed commits once before the M019
  writes, then those writers commit themselves). If a future writer
  service gains a no-commit variant, the seed should switch to it
  rather than wrapping commits in savepoints.
- 2026-09-30 (M054): seed cleanup rides the FK cascade from the four
  fixed `users` — farmers→farms→plots→states/signals all
  ondelete=CASCADE (M011–M019), so one scoped DELETE replaces five.
  Verified the cascade list with a grep of `ondelete="CASCADE"` before
  writing the fixture; do the same before any future cascade-based
  cleanup.
- 2026-09-30 (M054): **seed residue breaks the gate, not just the
  other way around (M012 inverted).** The CLI end-to-end check ran
  after gate #1; gate #2 then failed 8 tests that count global rows
  (officer/admin farm lists and every `ingest_*_for_all` sweep saw
  the 2 demo farms: totals 3–4 vs expected 1–2). The suite's migration
  round-trip wiped the residue at the end of the failing run, so the
  cleanup DELETE deleted 0 rows and gate #3 passed clean (713).
  **Rule: `workers/seed_demo` runs only AFTER the final gate, or the
  four fixed user ids get one scoped DELETE before any gate.**
- 2026-09-30 (M054): `plot` carries its own nullable `geo`/`area`
  (M015) — the seed intentionally fills farm geometry only; plot
  polygons remain "map it in the UI" data. If M056's spatial queries
  ever need plot-level geometry for demos, that's a seed extension,
  not a new milestone.
- 2026-09-30 (M055): **the error-unification blast radius was three
  assertions, not thirty** — most API tests only pin status codes, so
  the recorded M017/M020/M045 "dual dialect" debt turned out to be
  test-assertion debt in exactly 3 places (`test_farm_state` ×1,
  `test_whatif` ×2) plus the rotation echo in `test_auth`. When a
  debt entry says "clients rely on shape X", grep the *tests* first:
  they are usually the only clients, and the migration is smaller
  than the note suggests.
- 2026-09-30 (M055): **rate-limit tests must reset process state or
  they poison their neighbours** — the limiter is deliberately
  process-wide (no DI seam in the request path), so `tests/conftest.py`
  (the repo's first conftest) carries an autouse reset. Any future
  module-level mutable state needs the same treatment *before* its
  tests land, or the failure shows up in an unrelated file.
- 2026-09-30 (M055): **dependency order is a security control.**
  `_limit` is declared before `SessionDep` so a blocked brute-force
  never opens a session (FastAPI solves sub-dependencies in
  declaration order). Reordering params looks like style and isn't —
  the comment in the signature is load-bearing.
- 2026-09-30 (M055): the IDOR default-deny sweep caught `logout`
  immediately (422 where it demanded 401) — possession-based routes
  can't answer 401 to a request with no body. The allow-list treats
  it like `login`/`refresh`; `logout-all` (bearer) must stay OUT of
  the list. When adding any credential-bearing route, update
  `PUBLIC_OPERATIONS` in the same commit or the sweep fails by
  design — which is exactly what a regression guard should do.
- 2026-09-30 (M055): **rotation changes the client contract** —
  anything caching a refresh token must read the response each time.
  Recorded in the spec as a breaking change; the reuse-detection
  payoff (replay ⇒ family revoked) is tested in both directions
  (replayed old fails AND the rotated sibling fails AND fresh login
  still works — revocation is not a ban).
- 2026-09-30 (M055): `check.ps1` now runs bandit + pip-audit, so the
  D8/M035 "pin, audit, record" checklist is enforced mechanically.
  Note pip-audit needs network; a flaky network fails the gate (by
  design — a dependency scan you can skip isn't a scan).
- 2026-09-30 (M056): **the roadmap row flip is its own checklist step
  and M054/M055 both missed it** — specs said done, both were
  committed, ENGINEERING_STATE recorded them, yet the table still read
  `in-progress`. Corrected alongside M056's row. Lesson: verify the
  table with a grep after flipping, don't infer it from the spec
  header.
- 2026-09-30 (M056): the MODIS calendar cache is process-wide BY
  DESIGN (M027 proved `/dates` ignores the point — same 610 entries
  mid-ocean), so it is keyed by nothing; `reset_calendar_cache()` in
  the autouse conftest fixture also RECREATES the `asyncio.Lock` —
  loop-bound primitives must not cross per-test event loops (Python
  raises "bound to a different event loop" on cross-loop reuse under
  contention).
- 2026-09-30 (M056): **fetch/persist split, not session-per-task.**
  The parallelism that matters is the network phase; an `AsyncSession`
  can't be shared concurrently, so `for_all` = one point query
  (removing N per-farm centroid queries too) → Semaphore-bounded
  gather → serial `_persist_reading`. The rejected alternative
  (session per farm task) would open `ingest_concurrency` pool
  connections and complicate rollback isolation for no read-path gain.
  Every pre-existing `for_all` test passed unchanged — statuses,
  result order and batch isolation are the contract, and they survived
  the rewrite untouched.
- 2026-09-30 (M056): query budgets get ZERO headroom (exact measured
  counts, M019's `== 3` precedent) — headroom would let one accidental
  extra query through, the exact regression class. A future legitimate
  query change must edit the budget in the same commit, making the
  delta visible in review. Measured: `analyze_farm` 3 (= get_farm_state
  contract), `GET /farms` 4 (user, profile, count, list),
  `GET /farms/{id}` 2 (user, joined select), state endpoint 5 (user,
  authz, +3). Pool pre-ping does NOT surface at `before_cursor_execute`,
  so budgets are stable across cold/warm pools.
- 2026-09-30 (M056): the M007 `/ready` residual finally has an
  answer — measured in-process by hanging INSIDE
  `async with engine.connect()` (the checked-out state M007 couldn't
  reproduce), letting `wait_for`'s 2 s budget expire and asserting
  `pool.checkedout()` returns to baseline: CLEAN across runs. The
  earlier "not reproducible" note missed that the hang must hold a
  real connection — monkeypatching `get_engine` with a hanging fake
  never checks a connection out, so it can't exercise the
  release-under-cancellation path at all.
