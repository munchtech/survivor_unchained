#!/bin/bash
# The worktree's Godot import in its own Godot turn.   bash import.sh [log]
S="${OSCR:?set OSCR, the outfits scratch folder}/hs"
LOG="${1:-$S/import.log}"
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $T take godot "outfits lead: worktree import" --wait 60 >/dev/null 2>&1; do :; done
echo "import start $(date +%H:%M:%S)"
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)/godot"
timeout 2400 /c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe --headless --path . --import >"$LOG" 2>&1
echo "import exit $?"
$T give godot "outfits lead: worktree import" >/dev/null
echo "import end $(date +%H:%M:%S)"
sed 's/\x1b\[[0-9;]*m//g' "$LOG" | grep -E "Started|ERROR" | head -12
