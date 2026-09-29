# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "(none in progress) — M024 and M027, the only two unblocked P1 milestones, are both done; the remaining P1s are dependency-blocked (see Next milestone). Next milestone awaits a human pick: M030 (soil live, P2) or the P0 chain starting at M031."
Completed milestones: ["M001", "M002", "M003", "M004", "M005", "M006", "M007", "M008", "M009", "M010", "M011", "M012", "M013", "M014", "M015", "M016", "M017", "M018", "M019", "M020", "M021", "M022", "M023", "M024", "M025", "M026", "M027", "M028", "M029"]
Current implementation status: "M027 done: satellite live provider (NASA MODIS NDVI) — src/providers/satellite_live.py LiveSatelliteProvider registered (\"satellite\",\"live\") against the keyless ORNL DAAC TESViS REST service (MOD13Q1, Terra 16-day 250 m). TWO-REQUEST protocol: GET /MOD13Q1/dates (global composite calendar) → newest calendar_date ≤ today, then GET /MOD13Q1/subset for that single date with a 9×9 window (km=1, 231.66 m cell). Mapping: ndvi = mean of QA-valid pixels (pixel_reliability 0/1, raw ∈ [-2000,10000]) × 0.0001 @4dp, none usable → None; cloud_cover_pct = share of the window QA-flagged cloudy (3) @1dp (documented approximation — MOD13Q1 has no cloud band); captured_at = composite day 00:00 UTC; source = ornl-daac-modis-mod13q1. Taxonomy: timeout/transport/5xx/429 → ProviderUnavailable; other 2xx-adjacent 4xx (incl. upstream plain-text 400/404, trimmed to 200 chars), empty subset (ocean), missing bands/bad types → ProviderResponseInvalid. Same client-ownership shape as M024 (pooled httpx.AsyncClient, 20 s timeout, injectable, aclose()). No new dependencies. Settings default stays demo."
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
  - "P1 milestones M038, M051, M052, M053 are dependency-blocked: M038 needs M036/M037 (disease provider+assessment), M051 needs M045/M050 (what-if API + advisory UI), M052/M053 need M046/M037. None of their P0 predecessors (M031–M046) are started — spec them just-in-time per Section 8 before any of these can move."
Next milestone: "Human pick required. Options in roadmap order: (a) M030 — Soil live provider (P2, depends M029 met) — completes the live-provider trio; needs a keyless soil source researched the same way M027 did; (b) the P0 demo chain: M031 normalization → M032/M033/M034 engines → M035+ disease → M039+ advisory. No unblocked P1 remains (M024 + M027 done). Prior human-confirmed ordering (2026-09-28): P0s of the provider phase first, then P1s M024/M027, then P2 M030."
Last verification: "M027 gate PASSED with live dev DB (65432): ruff format OK, ruff check OK, mypy OK (104 files), pytest 403 passed / 0 skipped (40 new satellite-live tests); bandit -r -ll on src/providers + workers = 0; pip-audit clean (no new deps). Live (live_m027.py, real HTTP): 8/8 PASS — Nairobi ndvi 0.2731/0.0% cloud, Mombasa 0.3508/0.0%, Amazon rainforest 0.8581 (≥0.5 asserted), Oman desert 0.109 (≤0.3 asserted), Sydney 0.3947/66.7% cloud (all captured_at 2026-08-13); ocean (0,-140) → ProviderResponseInvalid; real upstream 404 → ProviderResponseInvalid with trimmed upstream text; closed port 127.0.0.1:9 → ProviderUnavailable."
Last test result: "pytest = 403 passed (satellite-live 40, weather-live 57, soil-ingestion 11, soil 15, satellite-ingestion 11, satellite 14, weather-ingestion 10, weather-demo 14, providers 15, farm-state-api 14, farm-state-service 10, state 14, idor 13, plots-API 13, farms-API 15, farmers-API 15, auth 14, health 9, rbac 11, root 4, config 8, db 4, redact 3, errors 8, logging 4, security 17, user 6, farm-model 11, farmer-model 8, plot-model 11, migrations 2, smoke 2)"
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
