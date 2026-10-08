#!/bin/bash
# The legal motion check against the outfits lead's worktree build (never the main checkout's).
#   bash run_outfit.sh <outfit> <tag> [clip ...]     no clips: all of them (about 45, ~10 min)
# One Godot turn per call, given back the moment the clips end. Pictures stay in the scratchpad
# (they carry test tints and, for calib, her bare: never commit or share them).
O="$1"; TAG="$2"; shift 2
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"  # (this worktree)
L="${OSCR:?set OSCR, the outfits scratch folder}/legal"
NAME="outfits lead: motion check, $O ($TAG)"
TURN="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
until $TURN take godot "$NAME" --wait 60 >/dev/null 2>&1; do :; done
echo "turn taken $(date +%H:%M:%S)"
export OUT="$L/$TAG/$O"
mkdir -p "$OUT"
if [ $# -gt 0 ]; then export CLIPS="$*"; fi
ONLY="$O" PROJECT=$WT/godot bash "$WT/tools/legal/motioncheck/run.sh" all >"$OUT/run_log.txt" 2>&1
$TURN give godot "$NAME" >/dev/null
echo "turn given back $(date +%H:%M:%S)"
echo "clips with no frames (a load failed?):"; awk '$3 == 0' "$OUT/run_log.txt"
grep -h -E "SCRIPT ERROR|Parse Error|SHADER ERROR" "$OUT"/log_*.txt | sort | uniq | head -10
python "$WT/tools/legal/motioncheck/count.py" "$OUT" 6 >/dev/null
cat "$OUT/summary.txt"
echo "every frame with any areola or strip pixel (frame, areola, strip, tucked, ring, closest cm):"
awk -F, 'NR>1 && ($2>0 || $3>0)' "$OUT/counts.csv"
echo OUTFITDONE
