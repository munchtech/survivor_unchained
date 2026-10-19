#!/bin/sh
# Godot turn: import, then ArmsDump. Usage: dump.sh <log>
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
LOG=$1
python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "anim38 A: arms dump" --wait 600 --stale-ok --root "$W" > "$LOG" 2>&1 || { echo "turn refused" >> "$LOG"; exit 1; }
"$G" --headless --path "$W/godot" --import >> "$LOG" 2>&1
"$G" --headless --path "$W/godot" -s res://tools_scenes/arms_dump.gd >> "$LOG" 2>&1
echo "exit $?" >> "$LOG"
python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "anim38 A: arms dump" --root "$W" >> "$LOG" 2>&1
