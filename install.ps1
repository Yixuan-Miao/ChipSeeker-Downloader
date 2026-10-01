$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $Root ".venv"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

function New-ChipSeekerVenv {
    $Py = Get-Command py -ErrorAction SilentlyContinue
    if ($Py) {
        & $Py.Source -3 -m venv --clear $VenvDir
    } else {
        $Python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $Python) {
            throw "Python 3 was not found. Install Python 3 and run install.ps1 again."
        }
        & $Python.Source -m venv --clear $VenvDir
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the ChipSeeker Downloader Python environment."
    }
}

if (-not (Test-Path $VenvPython)) {
    New-ChipSeekerVenv
} else {
    $VenvPip = Join-Path $VenvDir "Lib\site-packages\pip"
    if (-not (Test-Path $VenvPip)) {
        Write-Host "Repairing an incomplete downloader environment..." -ForegroundColor Yellow
        New-ChipSeekerVenv
    }
}

& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip." }
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install downloader dependencies." }

$FileClass = "ChipSeeker.DownloadTask"
$ExtensionKey = "HKCU:\Software\Classes\.csdl"
$ClassKey = "HKCU:\Software\Classes\$FileClass"
$CommandKey = Join-Path $ClassKey "shell\open\command"
$Launcher = Join-Path $Root "run_downloader.cmd"

New-Item -Path $ExtensionKey -Force | Out-Null
Set-Item -Path $ExtensionKey -Value $FileClass
New-Item -Path $ClassKey -Force | Out-Null
Set-Item -Path $ClassKey -Value "ChipSeeker Download Task"
New-ItemProperty -Path $ClassKey -Name "FriendlyTypeName" -Value "ChipSeeker Download Task" -PropertyType String -Force | Out-Null
New-Item -Path $CommandKey -Force | Out-Null
Set-Item -Path $CommandKey -Value ('"{0}" "%1"' -f $Launcher)

$ShellRefresh = Join-Path $env:WINDIR "System32\ie4uinit.exe"
if (Test-Path $ShellRefresh) {
    & $ShellRefresh -show
}

Write-Host ""
Write-Host "ChipSeeker Downloader installed." -ForegroundColor Green
Write-Host "Double-click any .csdl file to start a visible download session."
Write-Host "Opening the downloader without a file uses the newest .csdl in Downloads."
Write-Host "Installation folder: $Root"

