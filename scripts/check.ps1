# AgriN quality gate (decision D2): format check -> lint -> typecheck -> tests.
# Non-mutating: use `uv run ruff format .` to actually format.
# Invoke: powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
# (pwsh / PowerShell 7 is not on PATH on this host.)
$ErrorActionPreference = "Continue"

$failed = 0

function Invoke-Step {
    param([string]$Name, [string[]]$CmdArgs)
    Write-Host "==> $Name" -ForegroundColor Cyan
    & uv @CmdArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $Name (exit $LASTEXITCODE)" -ForegroundColor Red
        $script:failed = 1
    }
}

Invoke-Step "ruff format (check)" @("run", "ruff", "format", "--check", ".")
Invoke-Step "ruff lint"           @("run", "ruff", "check", ".")
Invoke-Step "mypy"                @("run", "mypy", ".")
Invoke-Step "pytest"              @("run", "pytest")

if ($failed -ne 0) {
    Write-Host "`nQuality gate FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "`nQuality gate PASSED" -ForegroundColor Green
exit 0
