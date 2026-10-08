#!/bin/bash
# Her body and outfits built with the helper bones into this worktree (a Blender turn),
# then imported and her skeleton re-dumped (a Godot turn).
#   bash build_helpers.sh            NOIMPORT=1 skips the Godot half
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2a9884e3e51609c
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/0b33992d-1e38-4eb8-80a1-d5c23b1a44e6/scratchpad/an
B=/c/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
W="animation: helpers build"
until $T take blender "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "blender turn $(date +%H:%M:%S)"
cd $WT
timeout 7000 "$B" -b "$S/heroine_built.blend" --python tools/assets/heroine_outfits.py -- godot/art/people/x --body godot/art/people/heroine.glb --helpers > "$S/build.log" 2>&1
echo "blender exit $?"
$T give blender "$W" >/dev/null
echo "blender done $(date +%H:%M:%S)"
grep -E "Error|Traceback|RIG|BODY |OUTFIT " "$S/build.log" | head -30
if [ -n "$NOIMPORT" ]; then echo BUILDDONE; exit 0; fi
W="animation: helpers import"
until $T take godot "$W" --wait 60 >/dev/null 2>&1; do :; done
echo "godot turn $(date +%H:%M:%S)"
cd $WT/godot
for k in 1 2 3; do timeout 1800 "$G" --headless --path . --import > "$S/import.log" 2>&1 && break; echo "import retry $k"; done
timeout 300 "$G" --headless --path . -s res://tools_scenes/anim_skeleton.gd -- "$WT/tools/anim/data/heroine_skeleton.json" > "$S/skel.log" 2>&1
echo "skeleton dump exit $?"
$T give godot "$W" >/dev/null
echo "godot done $(date +%H:%M:%S)"
sed 's/\x1b\[[0-9;]*m//g' "$S/import.log" | grep -E "ERROR" | head -12
echo BUILDDONE
