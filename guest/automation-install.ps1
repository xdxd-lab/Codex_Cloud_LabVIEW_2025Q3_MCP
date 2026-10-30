$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$labAutoBase = 'C:\Temp\LabVIEWAutomation'
$labAutoRoot = Join-Path $labAutoBase 'Zuehlke-v2.3.1'
$labAutoZip = Join-Path $labAutoBase 'Downloads\labview-mcp-v2.3.1.zip'
$labAutoState = Join-Path $labAutoBase 'installation-state.json'
$labAutoExpected = '34cffee146e3452dc391cbf6b2c3c2d2c079e3a63e72796c4770c39217cc3224'
New-Item -ItemType Directory -Force -Path $labAutoBase,(Split-Path $labAutoZip),$labAutoRoot | Out-Null
function Report-Stage([string]$stage, [hashtable]$details = @{}) {
    $record = @{stage=$stage; utc=[DateTime]::UtcNow.ToString('o'); root=$labAutoRoot; release='v2.3.1'; expected_sha256=$labAutoExpected}
    foreach ($key in $details.Keys) { $record[$key] = $details[$key] }
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $labAutoState -Encoding UTF8
    & curl.exe -fsS --connect-timeout 30 --max-time 120 -X POST --data-binary "@$labAutoState" 'http://10.0.2.2:8765/automation-state.json'
    Write-Host "Stage: $stage"
}
try {
    Report-Stage 'downloading'
    if (!(Test-Path -LiteralPath $labAutoZip) -or ((Get-FileHash -LiteralPath $labAutoZip -Algorithm SHA256).Hash.ToLower() -ne $labAutoExpected)) {
        & curl.exe -fS --connect-timeout 30 --max-time 1800 'http://10.0.2.2:8765/labview-mcp.zip' -o $labAutoZip
        if ($LASTEXITCODE -ne 0) { throw 'Pinned release download failed' }
    }
    $actual = (Get-FileHash -LiteralPath $labAutoZip -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $labAutoExpected) { throw 'Release SHA-256 mismatch; extraction refused' }
    Report-Stage 'extracting' @{zip_sha256=$actual}
    Expand-Archive -LiteralPath $labAutoZip -DestinationPath $labAutoRoot -Force
    Report-Stage 'checking_executables'
    $labAutoExe = Join-Path $labAutoRoot 'bin\LabVIEWMCP.exe'
    $labAutoPython = Join-Path $labAutoRoot 'bin\pylabview\python.exe'
    if (!(Test-Path -LiteralPath $labAutoExe) -or !(Test-Path -LiteralPath $labAutoPython)) { throw 'Release layout does not contain expected executables' }
    & curl.exe -fsS --connect-timeout 30 --max-time 120 'http://10.0.2.2:8765/mcp_stdio_http.py' -o (Join-Path $labAutoRoot 'mcp_stdio_http.py')
    if ($LASTEXITCODE -ne 0) { throw 'Private bridge transfer failed' }
    & curl.exe -fsS --connect-timeout 30 --max-time 120 'http://10.0.2.2:8765/automation-start.cmd' -o (Join-Path $labAutoBase 'automation-start.cmd')
    if ($LASTEXITCODE -ne 0) { throw 'Launcher transfer failed' }
    $labAutoVersion = (& $labAutoExe --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'MCP executable version probe failed' }
    $labAutoPythonVersion = (& $labAutoPython --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Bundled Python version probe failed' }
    $labAutoFirewall = $false
    $labAutoIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $labAutoPrincipal = New-Object Security.Principal.WindowsPrincipal($labAutoIdentity)
    if ($labAutoPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        $ruleName = 'LabVIEW MCP private QEMU host 36988'
        if (!(Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 36988 -LocalAddress '10.0.2.15' -RemoteAddress '10.0.2.2' -Program $labAutoPython -Profile Any | Out-Null
        }
        $labAutoFirewall = $true
    }
    Report-Stage 'installed_not_connected' @{mcp_version=$labAutoVersion; python_version=$labAutoPythonVersion; exe_sha256=(Get-FileHash -LiteralPath $labAutoExe -Algorithm SHA256).Hash.ToLower(); firewall_private_host_rule=$labAutoFirewall; bridge_port=36988; backend='pylabview'; labview_target='2025 Q3 64-bit'; auto_update=$false}
} catch {
    Report-Stage 'failed' @{error=$_.Exception.Message}
    throw
}
