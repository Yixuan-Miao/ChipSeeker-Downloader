$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "ChipSeeker - Save Open PDF Tabs" -ForegroundColor Cyan
Write-Host "-----------------------------------"
Write-Host "Open the selected PDFs in Edge or Chrome before continuing."
Write-Host ""
$rawCount = Read-Host "Number of open PDF tabs"

if ([string]::IsNullOrWhiteSpace($rawCount)) {
    Write-Host "No number entered. Nothing was changed." -ForegroundColor Yellow
    exit 0
}

$count = 0
if (-not [int]::TryParse($rawCount, [ref]$count) -or $count -lt 1 -or $count -gt 200) {
    Write-Host "Please enter a number from 1 to 200." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "The script will save and close $count PDF tabs." -ForegroundColor Green
Write-Host "After pressing Enter, click the RIGHTMOST PDF tab during the countdown."
Read-Host "Press Enter to start"

$shell = New-Object -ComObject WScript.Shell
for ($seconds = 5; $seconds -ge 1; $seconds--) {
    Write-Host "Starting in $seconds... click the browser PDF tab now."
    Start-Sleep -Seconds 1
}

for ($index = 1; $index -le $count; $index++) {
    Write-Host "[$index/$count] Saving the active PDF tab..."
    $shell.SendKeys("^s")
    Start-Sleep -Milliseconds 2200
    $shell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 2600
    $shell.SendKeys("^w")
    Start-Sleep -Milliseconds 900
}

Write-Host ""
Write-Host "Finished processing $count PDF tabs." -ForegroundColor Green
