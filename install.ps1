$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    $Py = Get-Command py -ErrorAction SilentlyContinue
    if ($Py) {
        & $Py.Source -3 -m venv (Join-Path $Root ".venv")
    } else {
        $Python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $Python) {
            throw "Python 3 was not found. Install Python 3 and run install.ps1 again."
        }
        & $Python.Source -m venv (Join-Path $Root ".venv")
    }
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Root "requirements.txt")

$FileClass = "ChipSeeker.DownloadTask"
$ExtensionKey = "HKCU:\Software\Classes\.csdl"
$ClassKey = "HKCU:\Software\Classes\$FileClass"
$CommandKey = Join-Path $ClassKey "shell\open\command"
$Launcher = Join-Path $Root "run_downloader.cmd"

New-Item -Path $ExtensionKey -Force | Out-Null
Set-Item -Path $ExtensionKey -Value $FileClass
New-Item -Path $ClassKey -Force | Out-Null
Set-Item -Path $ClassKey -Value "ChipSeeker Download Task"
New-Item -Path $CommandKey -Force | Out-Null
Set-Item -Path $CommandKey -Value ('"{0}" "%1"' -f $Launcher)

Write-Host ""
Write-Host "ChipSeeker Downloader installed." -ForegroundColor Green
Write-Host "Double-click any .csdl file to start a visible download session."
Write-Host "Installation folder: $Root"

