#!/bin/bash
# The Warden's and the Arcanist's finding clips on a new build, in one Godot turn, then counts.
#   bash findings.sh <folder tag>
TAG="$1"
NAME="legal: finding clips on the fit-fix build (af0973d5)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" --wait 30 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
T=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a/tools/legal/motioncheck
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3"
P=/c/Users/munch/Desktop/survivorsunchained/godot
OUT="$L/$TAG/warden" PROJECT="$P" ONLY=warden CLIPS="sprint_warden chain_haul chain_strike dash bull_rush cast_bolt axe_fore death_back leap axe_back warcry throw" \
  bash "$T/run.sh" all >"$L/$TAG.warden.txt" 2>&1
OUT="$L/$TAG/arcanist" PROJECT="$P" ONLY=arcanist CLIPS="arcanist_show chain_haul bull_rush cast_bolt axes_left axes_right daggers_fore sword_fore throw sword_heavy sword_back" \
  bash "$T/run.sh" all >"$L/$TAG.arcanist.txt" 2>&1
$TURN give godot "$NAME"
echo "turn given back $(date +%H:%M:%S)"
cat "$L/$TAG.warden.txt" "$L/$TAG.arcanist.txt" | awk '$3 == 0' | head
for o in warden arcanist; do python "$T/count.py" "$L/$TAG/$o" 6 | sed -n '5,60p'; done
echo FINDINGSDONE
