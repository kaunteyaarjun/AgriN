# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "(none in progress) — M031 (P0 normalization layer) is done and has unblocked the analysis engines: M032 and M034 are ready to start, M033 needs M032 as well. M030 (soil live) is still P2 and the remaining P1s stay dependency-blocked (see Next milestone)."
Completed milestones: ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M008", "M009", "M010", "M011", "M012", "M013", "M014", "M015", "M016", "M017", "M018", "M019", "M020", "M021", "M022", "M023", "M024", "M025", "M026", "M027", "M028", "M029", "M031"]
Current implementation status: "M031 done: data normalization layer (units/timeframes → Farm State) — src/services/normalize.py, a read-side PURE function layer (no DB, no I/O) that turns the raw farm_signal_caches.signals document into canonical pydantic models. normalize_signals(signals, now=, refreshed_at=) → NormalizedSignals(weather|satellite|soil|refreshed_at|refreshed_age_seconds|unknown_families|malformed_families); normalize_farm_state(FarmStateView) → NormalizedFarmState(view, signals) for the engines. Units: JSONB numbers only (bool/str/list/NaN/inf rejected before bounds), physical-range plausibility → None (temp −90..60 °C, humidity/cloud/soil-moisture 0..100, pH 0..14, NDVI −1..1, rainfall/wind/N ≥ 0), condition folded to the canonical 5-value vocabulary. Timeframes: SOURCE_PROFILES maps known source → rainfall_window_hours (demo 24, open-meteo 1 → rainfall_mm_per_day = mm×24/window) and ndvi_support_days (demo 1, MODIS 16); unknown source converts nothing. Provenance: per-family source/observed_at/age_seconds (naive timestamps assumed UTC, negative age allowed) — staleness thresholds deliberately left to M032+ per M019. Cache stays raw (no write-time change, no migration, no API change)."
Known bugs: []
Known security issues:
  - "Open (by design until M055): login/refresh have no rate limiting (flagged since M009); /docs+/redoc+/openapi.json public (documented hackathon decision, SECURITY.md in M059)."
Known performance issues:
  - "Live satellite ingest costs ~5.5 s/farm (2 HTTP calls; upstream ~3 s each) when satellite_provider=live; demo default unaffected. Live weather ~1 call. Sequential batch cost documented for M056."
Known resource/memory issues:
  - "Residual (documented, not reproducible locally): asyncio.wait_for cancelling /ready's check mid real-socket cleanup; SQLAlchemy pool handles greenlet cancellation — re-measure in M056. Refused-connection path asserted clean (checkedout()==0)."
Technical debt:
  - "Autogenerate migrations must ALWAYS be hand-reviewed — M008 caught a duplicated same-name CHECK constraint in the generated output."
  - "Error-shape inconsistency: Starlette route-mismatch 404 returns {detail} while AppError 404 returns {error_code,message} — no leak, optional HTTPException handler unification deferred to M055 (M017 finding). Both 422 flavors (pydantic {detail} vs AppError {error_code}) now coexist on purpose in farm-state routes (M020); unify in the same M055 pass."
Blocked tasks:
  - "P1 milestones M038, M051, M052, M053 are dependency-blocked: M038 needs M036/M037 (disease provider+assessment), M051 needs M045/M050 (what-if API + advisory UI), M052/M053 need M046/M037. Their P0 predecessors M032–M046 are still unstarted (M031 now done) — spec them just-in-time per Section 8 before any of these can move."
Next milestone: "Roadmap order: M032 Crop health analysis engine (P0, its only dependency M031 is met). M034 Crop recommendation engine (P0) is unblocked at the same time; M033 Farm risk engine needs M031 + M032, so it follows M032. M030 (soil live, P2) and the blocked P1s (M038/M051/M052/M053) remain outside the demo path. Engines are not lock-restricted, but they are architecturally significant — spec M032 just-in-time (Section 8) before coding."
Last verification: "M031 gate PASSED with live dev DB (65432): ruff format OK (109 files), ruff check OK, mypy OK (106 files), pytest 467 passed / 0 skipped (64 new normalization tests); bandit -r -ll on src + workers = 0; pip-audit clean (no new deps). No live check by design — the layer has no network or DB code path."
Last test result: "pytest = 467 passed (normalize 64, weather-live 57, satellite-live 40, soil 15, providers 15, state 14, weather-demo 14, satellite 14, farm-state-api 14, idor 13, plots-API 13, farms-API 15, farmers-API 15, auth 14, soil-ingestion 11, satellite-ingestion 11, weather-ingestion 10, farm-state-service 10, health 9, rbac 11, root 4, config 8, db 4, redact 3, errors 8, logging 4, security 17, user 6, farm-model 11, farmer-model 8, plot-model 11, migrations 2, smoke 2)"
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
| D8 | `httpx` **promoted from dev-only to runtime** dependencies at the same pin `0.28.1` (human-confirmed 2026-09-28) — live providers (M024+) need it at runtime; dev extra unchanged otherwise. |

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
