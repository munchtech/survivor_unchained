#!/bin/bash
# Close-ups of the warden's left cup through one sprint, with and without the marks, from the
# front, her left three-quarter and above (where the cup's inner top edge is seen).
cd /c/Users/munch/Desktop/survivorsunchained/godot || exit 1
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
V="front:0,1.42,0.55,1.40:32;three:35,1.45,0.55,1.40:32;above:15,1.75,0.55,1.40:34"
for m in 1 ""; do
  tag=$([ -n "$m" ] && echo marked || echo plain)
  env FOV=32 OUTFIT=warden HAIR=ponytail SPREAD=1 MARKS="$m" FRAMES=16 VIEWS="$V" FOLLOW=1 \
    timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$L/motioncheck2.gd" -- her/sprint_warden "$L/cupclose2/${tag}.png" \
    </dev/null >"$L/cupclose2/log_${tag}.txt" 2>&1
  echo "$tag $(ls "$L/cupclose" | grep -c "^${tag}_.*png")"
done
