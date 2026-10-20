#!/bin/sh
# Godot turn: build, import, then ArmsDump (anim-40). Usage: dump_idle2.sh <log>
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
LOG=$(realpath -m "$1")
python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "anim44 idle2: arms dump" --wait 900 --stale-ok --root "$W" > "$LOG" 2>&1 || { echo "turn refused" >> "$LOG"; exit 1; }
(cd "$W/godot" && dotnet build SurvivorUnchained.csproj -v q -nologo >> "$LOG" 2>&1); echo "build $?" >> "$LOG"
"$G" --headless --path "$W/godot" --import >> "$LOG" 2>&1
"$G" --headless --path "$W/godot" -s res://tools_scenes/arms_dump.gd >> "$LOG" 2>&1
echo "exit $?" >> "$LOG"
python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "anim44 idle2: arms dump" --root "$W" >> "$LOG" 2>&1
