@echo off
setlocal
set "MCP_AUTO_ROOT=C:\Temp\LabVIEWAutomation\Zuehlke-v2.3.1"
set "LABVIEWMCP_AIXML_BACKEND=pylabview"
set "LABVIEWMCP_LVVERSION=2025"
"%MCP_AUTO_ROOT%\bin\pylabview\python.exe" "%MCP_AUTO_ROOT%\mcp_stdio_http.py" --command "%MCP_AUTO_ROOT%\bin\LabVIEWMCP.exe" --cwd "%MCP_AUTO_ROOT%\bin" --host 10.0.2.15 --port 36988 --timeout 900 --allow-ip 127.0.0.1 --allow-ip 10.0.2.2 --allow-ip 10.0.2.15 --backend-arg=--aixml-backend --backend-arg=pylabview --backend-arg=--lvversion --backend-arg=2025 --log-dir "C:\Temp\LabVIEWAutomation\Logs"
echo MCP bridge exited with code %errorlevel%
pause
