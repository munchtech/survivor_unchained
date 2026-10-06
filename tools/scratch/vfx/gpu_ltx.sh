#!/usr/bin/env bash
# The LTX jobs (two tell takes, then the twelve skill clips), each waiting for
# enough free RAM first (the first try died at 2 GB free), retried once.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a63cd93fc73d5ed79
OUT=/c/Users/munch/Desktop/survivorsunchained/tools/comfy/out
VFX=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/vfx
cd "$WT"
free_gb() { powershell -NoProfile -Command "[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)"; }
wait_ram() {
  for i in $(seq 1 120); do
    f=$(free_gb | tr -d '\r')
    if [ "$f" -ge 11 ]; then echo "ram free ${f} GB"; return 0; fi
    echo "waiting for RAM (${f} GB free)"; sleep 30
  done
  return 1
}
wait_ram && python tools/comfy/sfx_clips.py "$OUT/sfx_ltx" tell_whistle tell_fuse && echo "tells made" || echo "tells failed"
for c in frost_spikes holy_ring blood_scythe moon_burst ice_shatter poison_cloud bramble_burst gold_flare fireball_impact dust_chop shadow_wisps leaf_burst; do
  for try in 1 2; do
    rm -rf "$OUT/clips/_$c"
    wait_ram
    if python tools/comfy/fx_clips.py "$OUT/clips" "$c"; then echo "clip $c made"; break; else echo "clip $c failed (try $try)"; sleep 30; fi
  done
done
python "$VFX/comfy_stat.py" free
echo "gpu chain done"
