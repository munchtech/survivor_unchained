#!/bin/bash
# Motion check for the mature-content survey: each outfit in her own run and
# sprint clips with jiggle on, eight frames a fifteenth of a second apart,
# from several angles. A scratch copy of the main checkout's lookdev scene
# (motioncheck.gd: lookdev plus her clip library as "her/"). Pictures go to
# the scratchpad. ONLY=outfit and VIEWS="name:orbit:fov ..." narrow a run.
cd /c/Users/munch/Desktop/survivorsunchained/godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
S="$L/motion2"
mkdir -p "$S"
OUTFITS="${ONLY:-reaver ranger warden arcanist}"
VIEWS="${VIEWS:-chest:0,1.45,1.3,1.30:35 below:0,0.95,1.2,1.25:42 hips:180,1.0,1.5,1.0:40 side:90,1.30,1.3,1.25:38}"
for o in $OUTFITS; do
  case $o in ranger) c=stalker;; *) c=$o;; esac
  for clip in "her/sprint_$c" "her/run_$c"; do
    cn="${clip#her/}"
    for v in $VIEWS; do
      n="${v%%:*}"; rest="${v#*:}"; orbit="${rest%:*}"; fov="${rest##*:}"
      env FOV=$fov OUTFIT=$o HAIR=ponytail ORBIT=$orbit FRAMES=8 timeout 300 "$G" --path . --resolution 960x540 -s "$L/motioncheck.gd" -- "$clip" "$S/${o}_${cn%%_*}_${n}.png" </dev/null >"$S/log_${o}_${n}.txt" 2>&1
      echo "$o $cn $n done"
    done
  done
done
echo MOTIONDONE
