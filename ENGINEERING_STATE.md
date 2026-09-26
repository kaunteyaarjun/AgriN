# ENGINEERING_STATE.md

> Kept truthful and current — updated at the end of **every** milestone
> (Master Engineering Prompt, Section 11). Never batch-update this file.

```yaml
Current milestone: "M001 — Repository bootstrap"
Completed milestones: []            # none yet
Current implementation status: "Phase A complete (kickoff files). Repo initialized; MILESTONES.md roadmap loaded; awaiting M001 implementation."
Known bugs: []
Known security issues: []
Known performance issues: []
Known resource/memory issues: []
Technical debt: []
Blocked tasks: []
Next milestone: "M001 — Repository bootstrap"
Last verification: "git init OK; MILESTONES.md + ENGINEERING_STATE.md created"
Last test result: "n/a (no tests yet)"
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

## Milestone commits

| Milestone | Commit |
|---|---|
| (kickoff) | — |
