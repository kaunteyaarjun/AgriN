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
| M001 | Repository bootstrap (structure, tooling, pre-commit) | P0 🔒 | — | not-started |
| M002 | Configuration & secrets management (env-based settings) | P0 | M001 | not-started |
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
