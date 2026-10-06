#!/bin/bash
# qa_shot.sh SAVE NAME SECONDS [game options...]
# Puts a QA save in the isolated QA user folder as the last slot, then runs the
# worktree's game with --continue and a screenshot.
set -e
SAVE="$1"; NAME="$2"; SECS="$3"; shift 3
SCR="C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad"
QA="C:/Users/munch/AppData/Roaming/Survivor Unchained QA/saves"
WT="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201"
GODOT="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
mkdir -p "$QA"
cp "$SCR/qa_saves/$SAVE.json" "$QA/slot0.json"
printf '{"last":0}' > "$QA/meta.json"
timeout 300 "$GODOT" --path "$WT/godot" --resolution 1920x1080 -- --continue --shot "$NAME" --seconds "$SECS" "$@" 2>&1 | grep -E "saved|ERROR|Exception|talk:|open " | head -20
