param(
    [string]$Browser = "",
    [int]$Seconds = 90
)

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$htmlPath = Join-Path $scriptDir "dropfix-highlight-showcase.html"

if (-not (Test-Path $htmlPath)) {
    throw "Cannot find highlight HTML at $htmlPath"
}

Write-Host "DropFix highlight page is ready: $htmlPath"
Write-Host "Tip: set $Seconds in the commandline to tune the suggested clip duration."

if ($Browser) {
    Start-Process $Browser $htmlPath
} else {
    Start-Process $htmlPath
}

Write-Host "Record this 90-second window with OBS/Screen recorder:"
Write-Host "1) Start recording"
Write-Host "2) Open the browser window"
Write-Host "3) Let the deck cycle through all scenes automatically"
Write-Host "4) Stop recording and trim to your preferred edit"

Start-Sleep -Seconds $Seconds
Write-Host "Suggested clip window complete. Save and export your video file."
