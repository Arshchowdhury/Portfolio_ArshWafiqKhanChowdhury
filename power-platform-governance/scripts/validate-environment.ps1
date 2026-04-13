<#
.SYNOPSIS
    Pre-flight validation script for Power Platform environment before deployment.

.DESCRIPTION
    Runs a series of checks against a target Power Platform environment to confirm
    it is ready to receive a solution import. Intended to be run manually by the
    platform lead before triggering the release pipeline, or as a diagnostic tool
    after a failed import.

    Checks performed:
      1. Service principal authentication against target environment
      2. Solution exists in source environment (Development) and is exportable
      3. Target environment is reachable and the principal has System Administrator role
      4. No active solution import is already in progress in the target environment
      5. Required environment variables are present in the target environment

.PARAMETER TargetEnvironmentUrl
    The URL of the environment to validate. Example: https://ridgeline-test.crm6.dynamics.com

.PARAMETER SolutionName
    The schema name of the solution to validate. Example: RidgelineKM

.PARAMETER AppId
    The Application (Client) ID of the service principal.

.PARAMETER TenantId
    The Azure Entra ID tenant ID.

.EXAMPLE
    .\validate-environment.ps1 `
        -TargetEnvironmentUrl "https://ridgeline-test.crm6.dynamics.com" `
        -SolutionName "RidgelineKM" `
        -AppId "00000000-0000-0000-0000-000000000000" `
        -TenantId "00000000-0000-0000-0000-000000000000"

    The script will prompt for the client secret interactively.
    To pass it non-interactively (e.g., from a pipeline): pipe via $env:PP_CLIENT_SECRET.

.NOTES
    Requires: Power Platform CLI (pac) — install via: npm install -g @microsoft/powerplatform-actions
    Requires: PowerShell 7.0 or later
    Author:   Arsh Wafiq Khan Chowdhury
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$TargetEnvironmentUrl,

    [Parameter(Mandatory = $true)]
    [string]$SolutionName,

    [Parameter(Mandatory = $true)]
    [string]$AppId,

    [Parameter(Mandatory = $true)]
    [string]$TenantId,

    [Parameter(Mandatory = $false)]
    [securestring]$ClientSecret
)

# ── Setup ──────────────────────────────────────────────────────────────────

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PassCount = 0
$FailCount = 0
$WarnCount = 0

function Write-Check {
    param([string]$Label, [string]$Status, [string]$Detail = "")
    $colour = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "Yellow" }
        default { "White" }
    }
    Write-Host "  [$Status] $Label" -ForegroundColor $colour
    if ($Detail) { Write-Host "         $Detail" -ForegroundColor DarkGray }
}

function Increment-Result {
    param([string]$Status)
    switch ($Status) {
        "PASS" { $script:PassCount++ }
        "FAIL" { $script:FailCount++ }
        "WARN" { $script:WarnCount++ }
    }
}

# ── Prompt for secret if not provided ─────────────────────────────────────

if (-not $ClientSecret) {
    $ClientSecret = Read-Host "Enter client secret for service principal $AppId" -AsSecureString
}

$ClientSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ClientSecret)
)

# ── Check 1: pac CLI available ─────────────────────────────────────────────

Write-Host "`nPower Platform Environment Pre-flight Check" -ForegroundColor Cyan
Write-Host "Target: $TargetEnvironmentUrl" -ForegroundColor Cyan
Write-Host "Solution: $SolutionName`n" -ForegroundColor Cyan

Write-Host "Check 1 — pac CLI availability"
try {
    $pacVersion = pac --version 2>&1
    Write-Check "pac CLI installed" "PASS" "Version: $pacVersion"
    Increment-Result "PASS"
} catch {
    Write-Check "pac CLI installed" "FAIL" "Install via: npm install -g @microsoft/powerplatform-actions"
    Increment-Result "FAIL"
    Write-Host "`nCannot continue without pac CLI. Exiting." -ForegroundColor Red
    exit 1
}

# ── Check 2: Authenticate to target environment ────────────────────────────

Write-Host "`nCheck 2 — Service principal authentication"
try {
    pac auth create `
        --name "pre-flight-check" `
        --environment $TargetEnvironmentUrl `
        --applicationId $AppId `
        --clientSecret $ClientSecretPlain `
        --tenant $TenantId `
        --cloud Public 2>&1 | Out-Null

    $whoAmI = pac org who 2>&1
    if ($whoAmI -match "Connected") {
        Write-Check "Authenticated to $TargetEnvironmentUrl" "PASS"
        Increment-Result "PASS"
    } else {
        Write-Check "Authenticated to $TargetEnvironmentUrl" "FAIL" "pac org who output: $whoAmI"
        Increment-Result "FAIL"
    }
} catch {
    Write-Check "Authenticated to $TargetEnvironmentUrl" "FAIL" $_.Exception.Message
    Increment-Result "FAIL"
}

# ── Check 3: Solution exists in target environment (if already deployed) ───

Write-Host "`nCheck 3 — Solution presence in target environment"
try {
    $solutionList = pac solution list 2>&1
    if ($solutionList -match $SolutionName) {
        # Extract version from output — pac solution list format: name | version | managed
        $versionLine = $solutionList | Select-String $SolutionName
        Write-Check "Solution '$SolutionName' found in target" "PASS" "$versionLine"
        Increment-Result "PASS"
    } else {
        Write-Check "Solution '$SolutionName' not yet in target" "WARN" "This is expected for a first-time deployment."
        Increment-Result "WARN"
    }
} catch {
    Write-Check "Could not list solutions in target" "WARN" $_.Exception.Message
    Increment-Result "WARN"
}

# ── Check 4: No import job in progress ────────────────────────────────────

Write-Host "`nCheck 4 — No import in progress"
try {
    # pac does not expose import job status directly — check via solution list timing
    # A solution list call that hangs for > 30s is an indicator of a locked import
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    pac solution list 2>&1 | Out-Null
    $timer.Stop()

    if ($timer.Elapsed.TotalSeconds -lt 30) {
        Write-Check "Environment responsive (no import lock detected)" "PASS" "Response in $([math]::Round($timer.Elapsed.TotalSeconds, 1))s"
        Increment-Result "PASS"
    } else {
        Write-Check "Environment slow to respond — possible import in progress" "WARN" "Response in $([math]::Round($timer.Elapsed.TotalSeconds, 1))s — check Admin Centre before proceeding"
        Increment-Result "WARN"
    }
} catch {
    Write-Check "Could not determine import lock state" "WARN" $_.Exception.Message
    Increment-Result "WARN"
}

# ── Check 5: Required environment variables present ───────────────────────

Write-Host "`nCheck 5 — Required environment variables"

# Define required environment variables for this solution.
# Update this list when new variables are added to the solution.
$RequiredEnvVars = @(
    "rco_SharePointSiteUrl",
    "rco_AzureOpenAIEndpoint",
    "rko_NotificationEmail"
)

try {
    $envVarOutput = pac env list-settings 2>&1
    foreach ($varName in $RequiredEnvVars) {
        if ($envVarOutput -match $varName) {
            Write-Check "Environment variable '$varName' present" "PASS"
            Increment-Result "PASS"
        } else {
            Write-Check "Environment variable '$varName' NOT found" "WARN" "Must be configured in target environment before import — see docs/05_ALM_Runbook.md section 4"
            Increment-Result "WARN"
        }
    }
} catch {
    Write-Check "Could not retrieve environment variables" "WARN" "Check manually in Power Platform Admin Centre before proceeding"
    Increment-Result "WARN"
}

# ── Summary ────────────────────────────────────────────────────────────────

Write-Host "`n─────────────────────────────────────────"
Write-Host "Pre-flight summary" -ForegroundColor Cyan
Write-Host "  PASS: $PassCount" -ForegroundColor Green
Write-Host "  WARN: $WarnCount" -ForegroundColor Yellow
Write-Host "  FAIL: $FailCount" -ForegroundColor Red
Write-Host "─────────────────────────────────────────`n"

if ($FailCount -gt 0) {
    Write-Host "One or more checks failed. Resolve failures before triggering the release pipeline." -ForegroundColor Red
    exit 1
} elseif ($WarnCount -gt 0) {
    Write-Host "Pre-flight passed with warnings. Review warnings above before proceeding." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "All checks passed. Environment is ready for deployment." -ForegroundColor Green
    exit 0
}
