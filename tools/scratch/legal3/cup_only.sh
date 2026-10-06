#!/bin/bash
# The Warden's sprint (five views, 16 frames) in one Godot turn, then the count.
#   bash cup_only.sh <folder tag>
TAG="$1"
NAME="legal: Warden sprint on the fit-fix build (af0973d5)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" --wait 30 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
T=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a/tools/legal/motioncheck
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3"
OUT="$L/$TAG/cup" PROJECT=/c/Users/munch/Desktop/survivorsunchained/godot bash "$T/run.sh" cup >"$L/$TAG.cup.txt" 2>&1
$TURN give godot "$NAME"
echo "turn given back $(date +%H:%M:%S)"
grep -h -E "SCRIPT ERROR|Parse Error|SHADER ERROR" "$L/$TAG"/cup/log_*.txt | sort | uniq | head -5
python "$T/count.py" "$L/$TAG/cup" 6 | sed -n '5,60p'
echo CUPDONE
