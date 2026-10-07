#!/bin/bash
# The outfits build in turns, in the outfits lead's own worktree (never the main checkout):
# Blender on this scratchpad's copy of heroine_built.blend (blender turn), then Godot's import
# and the turntable sheets (godot turn).
#   bash turn_build.sh                  OUTFITS="warden reaver" limits the sheets; NOSHEETS=1 skips them
#   AFTER="cmd" runs a command while the Godot turn is still held (close-ups, say)
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-afb34c385770877d3
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/hs
W="outfits lead: rebuild"
until $T take blender "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "blender turn $(date +%H:%M:%S)"
cd $WT
timeout 7000 "/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe" -b "$S/heroine_built.blend" --python tools/assets/heroine_outfits.py -- godot/art/people/x --body godot/art/people/heroine.glb > "$S/outfits.log" 2>&1
$T give blender "$W" >/dev/null
echo "blender done $(date +%H:%M:%S)"
grep -E "Error|Traceback|line [0-9]+|BODY|OUTFIT |PLATE CUP|HIDES" "$S/outfits.log" | head -30
until $T take godot "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "godot turn $(date +%H:%M:%S)"
cd $WT/godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
C="$S/cost"; mkdir -p "$C"
rm -f .godot/imported/heroine_outfit_*.gltf-*.md5 .godot/imported/heroine_outfit_*.gltf-*.scn
for k in 1 2 3; do timeout 900 "$G" --headless --path . --import >"$S/import.log" 2>&1 && break; echo "import retry $k"; done
if [ -z "$NOSHEETS" ]; then
for o in ${OUTFITS:-warden ranger arcanist reaver}; do
  for v in "0 f" "35 q" "150 b"; do set -- $v
    FOV=${FOVV:-14} OUTFIT=$o HAIR=ponytail NOLIFE=1 NOJIGGLE=1 ORBIT=$1,${CAM:-1.36,2.4,1.3} timeout 300 "$G" --path . --resolution 1000x1000 -s res://tools_scenes/lookdev.gd -- "Idle" "$C/s_${o}_$2.png" </dev/null >/dev/null 2>&1
  done
  (cd "$C" && python -c "
from PIL import Image
ims=[Image.open(f's_${o}_{k}.png').convert('RGB') for k in ('f','q','b')]
c=Image.new('RGB',(3000,1000)); [c.paste(im,(i*1000,0)) for i,im in enumerate(ims)]; c.save('sheet_${o}.png')")
done
fi
eval "${AFTER:-true}"
$T give godot "$W" >/dev/null
echo "godot done $(date +%H:%M:%S)"
echo BUILDDONE
