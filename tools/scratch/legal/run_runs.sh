#!/bin/bash
# After the full run: the plain run and sprint of the three rebuilt outfits not yet seen in
# them (the warden's waits for her new garment), into motion8, then the counts.
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
until grep -q "MOTIONDONE" "$L/motion8_run.log" 2>/dev/null; do sleep 10; done
cd /c/Users/munch/Desktop/survivorsunchained/godot || exit 1
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S="$L/motion8"
STAND="chest:0,1.45,1.3,1.30:35;left:45,1.40,1.2,1.28:36;side:90,1.30,1.3,1.25:38;below:0,0.95,1.2,1.25:42"
for o in arcanist ranger reaver; do
  case $o in ranger) c=stalker;; *) c=$o;; esac
  for clip in run_$c sprint_$c; do
    env FOV=38 OUTFIT="$o" HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=16 VIEWS="$STAND" \
      timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$L/motioncheck2.gd" -- "her/$clip" "$S/${o}_${clip}.png" \
      </dev/null >"$S/log_${o}_${clip}.txt" 2>&1
    echo "$o $clip $(ls "$S" | grep -c "^${o}_${clip}_.*png")" >> "$L/motion8_run.log"
  done
done
python "$L/count.py" "$S" 6 > "$L/motion8_counts.txt" 2>&1
echo RUNSDONE
