$ErrorActionPreference = "Stop"

$downloadsRoot = Join-Path $env:USERPROFILE "Downloads"
$sessionName = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = Join-Path $downloadsRoot (Join-Path "ChipSeeker" $sessionName)
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

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
Write-Host "Output: $outputDir"
Write-Host "After pressing Enter, click the RIGHTMOST PDF tab during the countdown."
Read-Host "Press Enter to start"

$shell = New-Object -ComObject WScript.Shell
for ($seconds = 5; $seconds -ge 1; $seconds--) {
    Write-Host "Starting in $seconds... click the browser PDF tab now."
    Start-Sleep -Seconds 1
}

for ($index = 1; $index -le $count; $index++) {
    Write-Host "[$index/$count] Saving the active PDF tab..."
    $beforeCount = @(Get-ChildItem -LiteralPath $outputDir -File -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
    $shell.SendKeys("^s")
    Start-Sleep -Milliseconds 2200

    # Move the native Save As dialog to this user's Downloads folder.
    $shell.SendKeys("%d")
    Start-Sleep -Milliseconds 300
    $shell.SendKeys($outputDir)
    Start-Sleep -Milliseconds 300
    $shell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 1200
    $shell.SendKeys("{ENTER}")

    $saved = $false
    for ($attempt = 1; $attempt -le 20; $attempt++) {
        Start-Sleep -Milliseconds 500
        $afterCount = @(Get-ChildItem -LiteralPath $outputDir -File -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
        if ($afterCount -gt $beforeCount) {
            $saved = $true
            break
        }
    }
    if (-not $saved) {
        Write-Host "No new PDF was detected. The current tab was left open." -ForegroundColor Red
        Write-Host "Confirm that this tab is the browser's native PDF viewer, then try again."
        Start-Process explorer.exe -ArgumentList $outputDir
        exit 2
    }

    $shell.SendKeys("^w")
    Start-Sleep -Milliseconds 900
}

Write-Host ""
Write-Host "Finished processing $count PDF tabs." -ForegroundColor Green
Write-Host "Saved to: $outputDir"
Start-Process explorer.exe -ArgumentList $outputDir
