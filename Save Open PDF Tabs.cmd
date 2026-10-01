@echo off
setlocal
set "ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%save_open_pdf_tabs.ps1"
if errorlevel 1 pause
