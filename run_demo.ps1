$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pnpmCommand = Get-Command pnpm.cmd -ErrorAction SilentlyContinue

if (-not $pnpmCommand) {
    throw "pnpm 10 is required. Install Node.js 20+ and run: corepack enable"
}

Set-Location -LiteralPath $projectRoot
& $pnpmCommand.Source install --frozen-lockfile
& $pnpmCommand.Source dev
