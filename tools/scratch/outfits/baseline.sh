#!/bin/bash
# The current build's baseline: the worktree's import (should be a no-op on the copied cache),
# then every outfit's full motion check, each in its own Godot turn.
#   bash baseline.sh <tag> [outfits]
TAG="$1"; OUTS="${2:-reaver warden arcanist ranger}"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-afb34c385770877d3
L=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/74e72383-70c7-41d5-8e96-2fad2ed58481/scratchpad/legal
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
if [ -z "$NOIMPORT" ]; then
  until $TURN take godot "outfits lead: worktree import" --wait 60 >/dev/null 2>&1; do :; done
  echo "import start $(date +%H:%M:%S)"
  (cd $WT/godot && timeout 1800 "$G" --headless --path . --import >"$L/import_$TAG.log" 2>&1); echo "import exit $?"
  $TURN give godot "outfits lead: worktree import" >/dev/null
  echo "import end $(date +%H:%M:%S)"
  grep -c -i "error" "$L/import_$TAG.log"
fi
for o in $OUTS; do
  bash "$L/run_outfit.sh" "$o" "$TAG" > "$L/${TAG}_$o.out" 2>&1
  echo "$o done $(date +%H:%M:%S)"
done
echo BASELINEDONE
