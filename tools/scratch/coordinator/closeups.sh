#!/bin/bash
# Close-ups for the outfit checks: each line "outfit angle camz dist targetz fov name"; out in $TEMP/hs/cu/<name>.png
cd /c/Users/munch/Desktop/survivorsunchained/godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S="$TEMP/hs/cu"; mkdir -p $S
while read o a cz d tz f n; do
  [ -z "$o" ] && continue
  env $EXTRA FOV=$f OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=$a,$cz,$d,$tz timeout 300 "$G" --path . --resolution 1920x1080 -s res://tools_scenes/lookdev.gd -- "${POSE:-Idle}" "$S/$n.png" </dev/null >/dev/null 2>&1
done < "${1:-/dev/stdin}"
