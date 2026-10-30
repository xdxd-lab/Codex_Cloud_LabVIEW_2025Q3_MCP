---
name: labview-mcp-2025q3
description: Install, configure, probe and troubleshoot LabVIEW MCP backends for the Windows 11 LabVIEW 2025 Q3 x64 guest, including stdio clients and a localhost HTTP bridge.
---

# LabVIEW MCP integration for this guest

## Establish facts first

- Read the latest `/workspace/windows-vm/diagnostics/cpu-test/result.md` and `/workspace/labview-automation/installation.json` if present.
- Query the actual VM and capture its screen internally. Do not send routine screenshots to the user.
- Keep the working QEMU CPU profile `max,vendor=GenuineIntel,pmu=off`. Do not revert to AMD/max. The earlier RDPMC crash is documented and is not a reason to repeat DISM/SFC.
- Pin downloaded releases, record source URL, commit/tag, SHA-256, license and minimum LabVIEW version. Review scripts before execution. A website login prompt does not prove that an official desktop package feed also requires login.

## Candidate backends

1. Zuehlke/labview-mcp: Windows x64 executable, MCP stdio, MIT. LabVIEW 2025 uses the older-version pylabview/ActiveX path. Some old install documentation still says 2026; inspect the pinned code and verify the subset live. Do not auto-update it.
2. JanGoebel/labview_assistant: native LabVIEW HTTP server; its missing MCP SDK and IG/JSONtext dependencies are recorded in `mcp-dependency-blocker.json`. SDK 2.2.3.26 requires LabVIEW >=26.1. SDK 2.1.0.20 is only a candidate for 25.3 until tested with the application. Do not upgrade LabVIEW merely to install an incompatible SDK.
3. labview-native-mcp: COM/VI Scripting Python implementation. Upstream validates 2021/2018 rather than 2025; treat as an experimental fallback, not an installed working backend.

## Installation and probing

- Windows executables and COM run in the Windows guest, not on the Linux host. A stdio server requires a local process client or an explicitly implemented bridge; copying a JSON config does not register a live ChatGPT tool.
- If installing a bridge, keep one stdio process and serialize calls. Preserve MCP protocol negotiation and session IDs when required. Restrict the guest bridge to the intended host path and forward the host port only on `127.0.0.1`.
- Test `initialize`, `notifications/initialized`, `tools/list`, a passive status tool, and a safe new-file test. Save response evidence with timestamp and actual error details. Use timeouts of 300 seconds or longer for TCG-backed calls.
- Use a fresh `C:\Temp\LabVIEWAutomation\` directory for testing. Check before save; do not overwrite `smoke.vi` or existing user work. For initial testing, do not run arbitrary user VIs or touch instruments.
- An authenticated public HTTPS connector for ChatGPT is a separate registration step. Do not expose an unrestricted local automation server publicly or claim that a local endpoint is already connected to the ChatGPT plugin catalog.

## Recover and stop

Confirm PID and command line before restoring helpers. Use the shared QMP lock. Never force reboot for slow initialization. Stop at an unresolved compatibility/authentication issue and report the exact verified limitation and what remains untested. Do not create recurring notifications unless requested; previously disabled automation stays disabled unless a new request calls for it.
