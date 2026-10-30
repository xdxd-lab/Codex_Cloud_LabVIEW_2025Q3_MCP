#!/bin/bash
set -euo pipefail
VM_DIR=/workspace/windows-vm
QEMU_ROOT=/workspace/vm-tools/root
SWTPM_ROOT=/workspace/windows-vm/win11-support/rootfs
export LD_LIBRARY_PATH="$SWTPM_ROOT/usr/lib/x86_64-linux-gnu/swtpm:$SWTPM_ROOT/usr/lib/x86_64-linux-gnu:$QEMU_ROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
test -f "$VM_DIR/OVMF_VARS.fd" || cp "$SWTPM_ROOT/usr/share/OVMF/OVMF_VARS_4M.ms.fd" "$VM_DIR/OVMF_VARS.fd"
mkdir -p "$VM_DIR/tpmstate"
ISO_ARGS=(-drive "media=cdrom,readonly=on,if=ide,index=2")
if [ -f "$VM_DIR/media/Windows11_Chinese_Traditional_x64.iso" ]; then
 ISO_ARGS=(-drive "file=$VM_DIR/media/Windows11_Chinese_Traditional_x64.iso,media=cdrom,readonly=on,if=ide,index=2")
elif [ -f "$VM_DIR/media/labview2025q3-x64.iso" ]; then
 ISO_ARGS=(-drive "file=$VM_DIR/media/labview2025q3-x64.iso,media=cdrom,readonly=on,if=ide,index=2")
fi
SWTPM_PID=""
if [ -r "$VM_DIR/swtpm.pid" ]; then
 SWTPM_PID="$(cat "$VM_DIR/swtpm.pid")"
fi
if [ -z "$SWTPM_PID" ] || ! kill -0 "$SWTPM_PID" 2>/dev/null; then
 "$SWTPM_ROOT/usr/bin/swtpm" socket --tpm2 --tpmstate dir="$VM_DIR/tpmstate" --ctrl type=unixio,path="$VM_DIR/swtpm.sock",mode=0600 --flags not-need-init,startup-clear --daemon --pid file="$VM_DIR/swtpm.pid"
fi
for i in {1..100}; do [ -S "$VM_DIR/swtpm.sock" ] && break; sleep 0.1; done
test -S "$VM_DIR/swtpm.sock"
exec "$QEMU_ROOT/usr/bin/qemu-system-x86_64" \
 -name LabVIEW-Windows11 \
 -L "$QEMU_ROOT/usr/share/qemu" \
 -machine q35,smm=on -accel tcg,thread=multi -cpu max,vendor=GenuineIntel,pmu=off -smp 2 -m 4096 \
 -vga none -device bochs-display,romfile= -device qemu-xhci -device usb-tablet \
 -drive if=pflash,format=raw,readonly=on,file="$SWTPM_ROOT/usr/share/OVMF/OVMF_CODE_4M.secboot.fd" \
 -drive if=pflash,format=raw,file="$VM_DIR/OVMF_VARS.fd" \
 -chardev socket,id=chrtpm,path="$VM_DIR/swtpm.sock" -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0 \
 -drive file="$VM_DIR/windows.qcow2",format=qcow2,if=ide,index=0,discard=unmap \
 -drive file="$VM_DIR/tools.iso",media=cdrom,readonly=on,if=ide,index=3 \
 "${ISO_ARGS[@]}" \
 -boot order=c,menu=on \
 -nic user,model=e1000,hostfwd=tcp:127.0.0.1:13389-:3389 \
 -vnc 127.0.0.1:1 -display none \
 -qmp unix:"$VM_DIR/qmp.sock",server=on,wait=off \
 -monitor none -serial none -d unimp -D /workspace/windows-vm/diagnostics/cpu-test/qemu-unimp-next.log \
 -pidfile "$VM_DIR/qemu.pid" -daemonize
