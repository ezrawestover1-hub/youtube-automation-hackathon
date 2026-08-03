[CmdletBinding()]
param(
    [string]$Browser = "",
    [ValidateRange(10, 300)]
    [int]$Seconds = 90,
    [ValidateRange(12, 30)]
    [int]$Fps = 30,
    [ValidateRange(640, 2560)]
    [int]$Width = 1366,
    [ValidateRange(360, 1600)]
    [int]$Height = 768,
    [string]$OutputName = "dropfix-highlight-showcase.mp4",
    [switch]$AutoRecord = $true,
    [switch]$Install = $false,
    [switch]$OpenOutput = $false
)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$htmlPath = Join-Path $scriptDir "dropfix-highlight-showcase.html"
$repoRoot = Split-Path -Path $scriptDir -Parent
$videoPath = Join-Path $repoRoot ("outputs\" + $OutputName)

if (-not (Test-Path $htmlPath)) {
    throw "Cannot find highlight HTML at $htmlPath"
}

if (-not (Test-Path (Split-Path $videoPath))) {
    New-Item -ItemType Directory -Path (Split-Path $videoPath) | Out-Null
}

if ($Install) {
    Write-Host "Installing/refreshing capture dependencies in $scriptDir"
    Push-Location $scriptDir
    try {
        npm.cmd install
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $scriptDir "node_modules"))) {
    Write-Host "Node modules not found. Running install automatically."
    Push-Location $scriptDir
    try {
        npm.cmd install
    } finally {
        Pop-Location
    }
}

if ($Browser) {
    Start-Process $Browser $htmlPath | Out-Null
} else {
    Start-Process $htmlPath | Out-Null
}

if (-not $AutoRecord) {
    Write-Host "DropFix highlight deck is ready: $htmlPath"
    Write-Host "Run recorder manually with: .\highlights\run-highlight-showcase.ps1 -Seconds 90"
    return
}

Write-Host "Auto-recording the highlight reel with headless browser capture."
Write-Host "Target: $videoPath"

$env:HIGHLIGHT_SECONDS = $Seconds.ToString()
$env:HIGHLIGHT_FPS = $Fps.ToString()
$env:HIGHLIGHT_WIDTH = $Width.ToString()
$env:HIGHLIGHT_HEIGHT = $Height.ToString()
$env:HIGHLIGHT_OUTPUT = $videoPath

Push-Location $scriptDir
try {
    & node .\record-dropfix-highlight.js
    if ($LASTEXITCODE -ne 0) {
        throw "render command failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

if (Test-Path $videoPath) {
    Write-Host "Rendered video: $videoPath"
    if ($OpenOutput) {
        Start-Process $videoPath | Out-Null
    }
} else {
    throw "Render did not produce an output file. Check logs above."
}
