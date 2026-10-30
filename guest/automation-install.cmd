@echo off
setlocal
if not exist C:\Temp\LabVIEWAutomation mkdir C:\Temp\LabVIEWAutomation
curl.exe -fsS --connect-timeout 30 --max-time 120 http://10.0.2.2:8765/automation-install.ps1 -o C:\Temp\LabVIEWAutomation\automation-install.ps1
if errorlevel 1 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Temp\LabVIEWAutomation\automation-install.ps1
echo Installation script exit code: %errorlevel%
pause
