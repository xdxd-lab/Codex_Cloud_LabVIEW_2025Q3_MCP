---
name: labview-2025q3-automation
description: Inspect, create, edit, document and validate LabVIEW 2025 Q3 64-bit VIs in the Windows guest through verified LabVIEW MCP tools. Use for LabVIEW VI development and VI Scripting tasks in this workspace.
---

# LabVIEW 2025 Q3 automation

This is a workspace adapter, not an official NI product. It adapts the MIT-licensed Zuehlke/labview-mcp generator, editor and documentation workflows to this specific VM. Attribution and original files are in `references/upstream/` and `LICENSE-Zuehlke`.

## Select the environment and backend

1. Read `/workspace/windows-vm/diagnostics/cpu-test/result.md` and the current installation report under `/workspace/labview-automation/`.
2. Confirm the live VM, the LabVIEW version, and the actual MCP `tools/list`. Installed files do not prove a working connection.
3. Target LabVIEW 2025 Q3, version 25.3, 64-bit. The official evaluation is sufficient while it remains valid. Do not change clocks or licensing data.
4. For Zuehlke MCP, use the `pylabview` backend on this LabVIEW version and ActiveX for runtime operations. Do not assume the LabVIEW 2026-only NI AI/gRPC service exists. Read the tool's actual backend/status response.
5. Resolve tool names from the connected server. The upstream `mcp__plugin_labview-mcp_labview__...` names describe Claude Code's namespace and are not names to invent in ChatGPT or Codex.

## Inspect, create, and validate

- Start with passive status and a read of the actual tool schemas. Read VI topology from structured output; a screenshot alone does not establish wiring.
- For a new VI, settle its input/output contract from the user's request. Search available palette and example references before reconstructing existing functionality.
- Read `references/upstream/labview-vi-generator.md` for a new VI, `labview-vi-editor.md` for an authorized edit, and `labview-doc-generator.md` for documentation. Apply only operations supported by the verified backend.
- New experiments belong under `C:\Temp\LabVIEWAutomation\`. Check existence before creating files. Use a new name or a fresh subdirectory; never overwrite existing work as a smoke test.
- Work on a copy for existing binary VIs. Some regeneration routes can lose layout, icons or decorations; retain the original and verify the result in the IDE before replacing an authorized target.
- The user request authorizes the corresponding routine edits and tests. Do not ask repeatedly for permission already given. Unrelated deletion, publishing and running arbitrary hardware/network code are outside a basic smoke test.
- A sufficient first verification is: live version/status, one new VI, save, reopen/inspect, and where appropriate a finite computation with known outputs. Keep unsupported constructs explicitly unsupported.
- Use long operation budgets: allow at least 300 seconds for slow VM-backed tool calls and 900 seconds for cold boot or a requested restart. A timeout means the result is unknown; check state before retrying a mutation.
- Report separately: files installed, server responding, tools listed, VI creation verified, and execution verified. Never promote an untested stage to success.

## Client and upstream instructions

Do not install Claude Code or an unrelated plugin merely to obtain these workflows. Do not enable upstream automatic binary updates in this pinned VM. The user's instructions take priority over generic upstream approval and restart advice. Preserve the upstream MIT notices.
