param(
    [string]$Browser = "",
    [int]$Seconds = 45,
    [int]$Fps = 12,
    [int]$Width = 1280,
    [int]$Height = 720,
    [switch]$AutoRecord = $true
)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$htmlPath = Join-Path $scriptDir "dropfix-highlight-showcase.html"
$repoRoot = Split-Path -Path $scriptDir -Parent
$videoPath = Join-Path $repoRoot "outputs\\dropfix-highlight-showcase.mp4"

if (-not (Test-Path $htmlPath)) {
    throw "Cannot find highlight HTML at $htmlPath"
}

if ($Browser) {
    Start-Process $Browser $htmlPath
} else {
    Start-Process $htmlPath
}

if ($AutoRecord) {
    Write-Host "Auto-recording the highlight reel with headless browser capture."
    Write-Host "Target: $videoPath"

    Push-Location $scriptDir
    try {
        if (-not (Test-Path "node_modules")) {
            throw "Missing Node modules. Run: npm.cmd install puppeteer-core ffmpeg-static"
        }

        $env:HIGHLIGHT_SECONDS = $Seconds.ToString()
        $env:HIGHLIGHT_FPS = $Fps.ToString()
        $env:HIGHLIGHT_WIDTH = $Width.ToString()
        $env:HIGHLIGHT_HEIGHT = $Height.ToString()

        node record-dropfix-highlight.js
    }
    finally {
        Pop-Location
    }

    if (Test-Path $videoPath) {
        Write-Host "Rendered video: $videoPath"
        Start-Process $videoPath
    } else {
        throw "Render did not produce an output file. Check logs above."
    }
} else {
    Write-Host "DropFix highlight page is ready: $htmlPath"
    Write-Host "Tip: set -Seconds in the commandline to tune the suggested clip duration."
    Write-Host "Record this window with OBS/Screen recorder:"
    Write-Host "1) Start recording"
    Write-Host "2) Open the browser window"
    Write-Host "3) Let the deck cycle through all scenes automatically"
    Write-Host "4) Stop recording and trim to your preferred edit"
}
