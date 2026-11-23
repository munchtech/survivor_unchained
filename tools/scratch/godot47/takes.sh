#!/bin/bash
# The trial's takes on one engine: the 12-shot movement harness (all takes), the den perf trace x4 (the first a shader-cache warm-up), the den film.
#   bash tools/scratch/godot47/takes.sh <console exe> <tag: g45|g47>
# Before each block it logs every Godot/Blender process running (another lane's would spoil the numbers).
set -u
GODOT_EXE="$1"; TAG="$2"
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
LOG="$WT/godot/.shots/godot47/takes_$TAG.log"
mkdir -p "$WT/godot/.shots/godot47"
cd "$WT"
others() { echo "[$(date +%T)] running before $1:"; tasklist //FO CSV //NH | grep -iE '^"(godot|blender)' || echo "  none"; }
export GODOT="$GODOT_EXE"
{
others "moves12"
TURN_LABEL="p1-godot47: moves12 $TAG" MOVES_OUT="moves12_$TAG" python tools/motion/move_baseline.py all
printf '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="SurvivorUnchainedPerf"\n' > godot/override.cfg
others "perf"
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "p1-godot47: perf $TAG" --wait 1800 --stale-ok
python tools/perf/run.py den --tag "$TAG" --repeat 4
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "p1-godot47: perf $TAG"
others "film"
python tools/scratch/godot47/den_film.py "$TAG" 45
rm -f godot/override.cfg
echo "TAKES DONE $TAG"
} > "$LOG" 2>&1
