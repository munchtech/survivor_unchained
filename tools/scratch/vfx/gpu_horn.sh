#!/usr/bin/env bash
# The dead's tell_horn takes (LTX audio), once there is RAM to spare; ComfyUI freed after.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a560452c597415545
OUT=/c/Users/munch/Desktop/survivorsunchained/tools/comfy/out
VFX=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/vfx
cd "$WT"
for i in $(seq 1 240); do
  f=$(powershell -NoProfile -Command "[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)" | tr -d '\r')
  if [ "$f" -ge 11 ]; then echo "ram free ${f} GB"; break; fi
  sleep 30
done
python tools/comfy/sfx_clips.py "$OUT/sfx_ltx" tell_horn && echo "horn made" || echo "horn failed"
python tools/comfy/fx_sprites.py make palm_print && echo "palm sprites made" || echo "palm sprites failed"
python "$VFX/comfy_stat.py" free
echo "horn chain done"
