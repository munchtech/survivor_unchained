#!/bin/bash
# The worktree's Godot import in its own Godot turn.   bash import.sh [log]
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/hs
LOG="${1:-$S/import.log}"
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $T take godot "outfits lead: worktree import" --wait 60 >/dev/null 2>&1; do :; done
echo "import start $(date +%H:%M:%S)"
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-afb34c385770877d3/godot
timeout 2400 /c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe --headless --path . --import >"$LOG" 2>&1
echo "import exit $?"
$T give godot "outfits lead: worktree import" >/dev/null
echo "import end $(date +%H:%M:%S)"
sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -E "Started|ERROR" | head -12
