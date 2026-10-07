#!/bin/bash
# The Warden's strap and pauldron at a bust close-up, under shader and AA variants, in one
# Godot turn. Each variant: "<shader file in hs/> <tag> [K=V ...]". The worktree's outfit
# shader is restored to hs/outfit_keep.gdshader afterwards.
#   bash sparkle.sh <outdir> "<cam line: outfit angle camz dist targetz fov>" "<variant>" ...
OUTD="$1"; CAM="$2"; shift 2
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-afb34c385770877d3
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/hs
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
N="outfits lead: sparkle variants"
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
SH=$WT/godot/shaders/heroine_outfit.gdshader
cp "$SH" "$S/outfit_keep.gdshader"
mkdir -p "$OUTD"
until $T take godot "$N" --wait 60 >/dev/null 2>&1; do :; done
cd $WT/godot
set -- "$@"
for v in "$@"; do
  read -r shf tag rest <<< "$v"
  cp "$S/$shf" "$SH"
  read -r o a cz d tz f <<< "$CAM"
  env $rest FOV=$f OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=$a,$cz,$d,$tz timeout 300 "$G" --path . --resolution ${RES:-1920x1080} -s res://tools_scenes/lookdev.gd -- "Idle" "$OUTD/$tag.png" </dev/null >"$OUTD/log_$tag.txt" 2>&1
  echo "$tag $(grep -c "SHADER ERROR" "$OUTD/log_$tag.txt") shader errors"
done
cp "$S/outfit_keep.gdshader" "$SH"
$T give godot "$N" >/dev/null
echo SPARKLEDONE
