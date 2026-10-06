#!/bin/bash
# One outfit's full motion check in one Godot turn (about 45 clips), then the count.
#   bash run_outfit.sh <outfit> <folder tag>       e.g. run_outfit.sh warden tuck1
# Pictures go to the scratchpad only. The turn is given back the moment the clips end.
O="$1"; TAG="$2"
NAME="legal: motion check, $O, all clips (af0973d5)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" --wait 30 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
T=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a/tools/legal/motioncheck
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3"
export OUT="$L/$TAG/$O"
mkdir -p "$OUT"
ONLY="$O" PROJECT=/c/Users/munch/Desktop/survivorsunchained/godot bash "$T/run.sh" all >"$OUT/run_log.txt" 2>&1
$TURN give godot "$NAME"
echo "turn given back $(date +%H:%M:%S)"
echo "clips with no frames (a load failed?):"; awk '$3 == 0' "$OUT/run_log.txt"
grep -h -E "SCRIPT ERROR|Parse Error|SHADER ERROR" "$OUT"/log_*.txt | sort | uniq | head -10
python "$T/count.py" "$OUT" 6 >/dev/null
cat "$OUT/summary.txt"
echo OUTFITDONE
