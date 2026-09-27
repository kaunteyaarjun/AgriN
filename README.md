# AgriN

AgriN is a self-hostable digital agriculture intelligence platform: it turns farm
geometry, weather, satellite/NDVI and soil signals into crop-health and risk
insights, disease triage, structured decisions, AI advisories and what-if
simulations for farmers and extension officers — as one modular-monolith
FastAPI service plus a single React SPA.

Development setup, commands and docs will be expanded in later milestones
(see `DEVELOPMENT.md` and the final documentation pass); for now: `uv sync
--extra dev`, then `powershell -NoProfile -ExecutionPolicy Bypass -File
scripts/check.ps1` runs the full quality gate.

Dev database: `docker compose up -d db` starts Postgres 16 on host port
`55432` (native Postgres already uses 5432/5433 here). Copy `.env.example`
to `.env`; integration tests skip automatically when the DB is unreachable.
