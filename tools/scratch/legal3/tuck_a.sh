#!/bin/bash
# The tuck build's first batch, in one Godot turn: where each outfit's tucked skin lies
# (tuckcalib), the codes' calibration, the false-positive check and the Warden's sprint.
#   bash tuck_a.sh <folder tag>
TAG="$1"
NAME="legal: tuck build, calibration and codes (af0973d5)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" --wait 30 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
T=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a/tools/legal/motioncheck
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3"
P=/c/Users/munch/Desktop/survivorsunchained/godot
for ph in tuckcalib calib fp cup; do
  OUT="$L/$TAG/$ph" PROJECT="$P" bash "$T/run.sh" "$ph" >"$L/$TAG.$ph.txt" 2>&1
  echo "$ph done $(date +%H:%M:%S)"
done
$TURN give godot "$NAME"
echo "turn given back $(date +%H:%M:%S)"
grep -h "legal marks" "$L/$TAG"/calib/log_*.txt "$L/$TAG"/tuckcalib/log_*.txt | sort | uniq
grep -h -E "SCRIPT ERROR|Parse Error|SHADER ERROR" "$L/$TAG"/*/log_*.txt | sort | uniq | head -10
for ph in tuckcalib calib fp cup; do echo "== $ph"; python "$T/count.py" "$L/$TAG/$ph" 6 | sed -n '5,40p'; done
echo BATCHDONE
