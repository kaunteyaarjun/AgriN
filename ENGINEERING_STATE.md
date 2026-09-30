# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "(none in progress) — M054 (deterministic demo seed) is done: uv run python -m workers.seed_demo populates the dev DB with a fixed world (4 users: admin/officer/2 farmers @agrin.demo, 2 farmers profiles, 2 farms with PostGIS rectangles, 4 plots with crop state via M019 set_plot_state, 2 signal caches via put_signals) keyed by uuid5 over a fixed namespace — re-running upserts in place, never duplicates, never cascade-deletes. Timestamps are seed-relative (observed_at = now-30min, planted_on = today-N days); content/sources fixed (demo-*-v1). Password from Settings.demo_password; dev falls back to the documented default, prod refuses to guess. Next per roadmap: M055 (auth hardening: rate limiting, refresh-token logout/revocation, unified AppError envelope, structured agrin.audit log events, bcrypt pin revisit) → M056 (perf) → M057 (test/CI consolidation, backend scope). Frontend chain M046-M053 remains 🔒 blocked on human approval. Remaining locks: M042 (LLM live), M046 (frontend), M058."
Completed milestones: ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M008", "M009", "M010", "M011", "M012", "M013", "M014", "M015", "M016", "M017", "M018", "M019", "M020", "M021", "M022", "M023", "M024", "M025", "M026", "M027", "M028", "M029", "M031", "M032", "M033", "M034", "M035", "M036", "M037", "M039", "M040", "M041", "M043", "M044", "M045", "M054"]
Current implementation status: "M054 done: the demo seed. New src/services/demo_seed.py: seed_demo(session, *, password, now=None) — uuid5(SEED_NAMESPACE, key) fixed ids for 4 users/2 farmers/2 farms/4 plots, ORM upserts for those rows, M019 set_plot_state + put_signals for crop state and signal caches (commits inside), returns SeedSummary; resolve_demo_password(settings) uses Settings.demo_password else DEV_DEMO_PASSWORD and raises in env=prod; farm geo via ST_GeomFromGeoJSON (M014 pattern), east/west polygons with fixed per-farm signal values (sources demo-*-v1). New workers/seed_demo.py CLI (no argparse — password never on a process command line) prints summary + credentials. Settings gains demo_password (SecretStr|None), .env.example documents DEMO_PASSWORD. New tests/services/test_demo_seed.py (8): 4 resolver tests + idempotency/roles/non-blind/password-rotation DB tests. No DB changes, no API changes, no new deps."
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
  - "P1 milestones M051-M053 are dependency-blocked: M051 (what-if UI) needs M050 (M045 done), M052/M053 need M046. M038 (disease live model) waits on a live-model decision. P0s remaining: M046-M050 (frontend chain, 🔒 human checkpoint first), M055-M057 (backend scope, unblocked — M055 next). M054 now done."
Next milestone: "M055 (auth & hardening, P0, deps M008/M009/M017 met): JIT spec covering the locked decisions — (1) in-process sliding-window rate limiter on login/refresh, NO new dependency, (2) refresh-token revocation/logout (one migration), (3) unify error shapes to the AppError {error_code, message} envelope (update tests; both 422 flavors recorded in M045), (4) structured agrin.audit log events instead of a table, (5) bcrypt pin/work-factor revisit (D3), /docs flag revisit (M007), add bandit+pip-audit to scripts/check.ps1. Then M056 (perf: live satellite ingest ~5.5s/farm, sequential batch cost, /ready wait_for residual, query-count regressions) → M057 (backend scope: consolidate ~12 duplicated API test fixtures into conftest — 713 tests must stay 713 — plus .github/workflows/ci.yml with postgis service). Frontend chain M046-M053 and M042/M058 remain locked on human approval."
Last verification: "M054 final gate PASSED with live dev DB (65432), run on a clean schema BEFORE the commits: ruff format OK (147 files), ruff check OK, mypy OK (144 sources), pytest 713 passed / 0 skipped (8 new: tests/services/test_demo_seed.py); bandit -r -ll on src + workers = 0; pip-audit clean — no new dependencies, no migration, no API changes. Sequence this milestone: gate #1 green → workers/seed_demo.py run twice end-to-end (identical summaries: users=4 farmers=2 farms=2 plots=4 plot_states=4 signal_caches=2, proving idempotency live) → gate #2 FAILED 8 counting tests on the seed residue → migration round-trip auto-wiped the rows → gate #3 green (see Notes)."
Last test result: "pytest = 713 passed (demo-seed 8, whatif-API 11, test_whatif 26, analysis 7, advisory-API 5, advisory 17, llm 24, decision 21, disease-engine 18, engines-health 38, recommend 22, risk 27, disease-provider 12, images-API 10, normalize 64, weather-live 57, satellite-live 40, soil 15, providers 15, state 14, weather-demo 14, satellite 14, farm-state-api 14, idor 13, plots-API 13, farms-API 15, farmers-API 15, auth 14, soil-ingestion 11, satellite-ingestion 11, weather-ingestion 10, farm-state-service 10, health 9, rbac 11, root 4, config 8, db 4, redact 3, errors 8, logging 4, security 17, user 6, farm-model 11, farmer-model 8, plot-model 11, migrations 2, smoke 2)"
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
