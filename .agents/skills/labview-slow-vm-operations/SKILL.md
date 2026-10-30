---
name: labview-slow-vm-operations
description: Operate this slow QEMU TCG Windows 11 LabVIEW guest using serialized QMP input, reliable English text entry, long waits and disk headroom monitoring.
---

# Slow Windows/LabVIEW VM operations

- VM directory: `/workspace/windows-vm`. Read `diagnostics/cpu-test/result.md` first and verify live processes; an environment restore can preserve files while losing the VM process.
- Preserve `-cpu max,vendor=GenuineIntel,pmu=off`, disk discard/unmap, EFI and TPM state. Do not change clocks or remove required NI Security Update KB67L8LCQW.
- Use `qmp.py`, `qmp-click.py` and `type-text.py`, which share `qmp-client.lock`. Click coordinates are absolute USB-tablet coordinates. Do not use the legacy VNC pointer implementation or independent clients without the same lock.
- Run dialog: Win+R, wait at least 7 seconds, confirm it actually appeared, Ctrl+A, type, then Enter. Wait for a real UAC prompt before accepting it. In file dialogs verify English IME (`英`); a single Shift toggles Chinese/English. Confirm the full path before submitting when input was uncertain.
- Allow at least 15 minutes for boot after normal restart. Initial LabVIEW/NI/.NET loading can also take several minutes. Observe screen, CPU activity, disk byte increments and errors; `QMP running` alone does not prove the guest desktop is responsive.
- Check host free space separately from guest C: free space. Never compact or reopen the active qcow2 to recover space. Before removing disposable installer media, preserve official source/hash and needed packages, eject the exact CD through QMP, verify it has no inserted medium, then remove the file. Never delete the Windows disk, EFI state or TPM state as routine cleanup.
- Keep the host disk guard if applicable. If its `space-guard-triggered.json` exists, resolve host capacity before resuming. Do not automatically resume a space-paused VM into the same full disk.
- Report brief Traditional Chinese status changes; provide a key screenshot only when the requested goal is completed. Do not send repeated unchanged screenshots.
