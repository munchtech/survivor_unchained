#!/bin/bash
# Import the worktree's Godot project, then dump her skeleton from the new body.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/43e8c2e6-36a3-4fd7-8ca4-39c475e24666/scratchpad/a38
python $W/tools/turn.py take godot "animation 38: import + skeleton dump" --wait 900 --stale-ok --root $W || { echo "NO TURN"; exit 1; }
cd $W/godot
timeout 1800 "$G" --headless --path . --import > $S/import.log 2>&1; echo IMPORT $?
cp $W/tools/anim/data/heroine_skeleton.json $S/heroine_skeleton_old.json
timeout 300 "$G" --headless --path . -s res://tools_scenes/anim_skeleton.gd -- $W/tools/anim/data/heroine_skeleton.json > $S/dump.log 2>&1; echo DUMP $?
python $W/tools/turn.py give godot "animation 38: import + skeleton dump" --root $W
echo STEP DONE
