#!/usr/bin/env bash
# frame-pacing-4 item 2: den perf legs (the upgrade lane's leg47.sh), 4.5.1 next4 (main checkout, run only) against this worktree's
# 4.7.2 export, uncapped and with --perf-vsync. usage: i2.sh <4.7.2 export name> <tag>:<45|47>:<u|v>...
# Summary (frames.py per leg) appended to godot/.shots/pacing4/i2_summary.txt ; csv/json/log in godot/.shots/pacing47/.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
N="$1"; shift
S=$WT/godot/.shots/pacing4/i2_summary.txt
for leg in "$@"; do
  IFS=: read tag eng mode <<< "$leg"
  D=$WT/release/godot/$N; [ "$eng" = 45 ] && D=/c/Users/munch/Desktop/survivorsunchained/release/godot/next4
  X=""; [ "$mode" = v ] && X="--perf-vsync"
  { echo "=== $tag engine $eng mode $mode exe $D"; PERF_FOR=900 QUIET_WAIT=7200 bash $WT/tools/scratch/godot47/leg47.sh $D $tag --perf-until den --perf-jit --veteran 9 --move-new --move-ab $X 2>&1 | cut -c1-220
    grep -a "fx warm-up" $WT/godot/.shots/pacing47/$tag.log | sed 's/; then.*//' | cut -c1-260
    python $WT/tools/perf/frames.py $WT/godot/.shots/pacing47/$tag.csv 2>&1 | cut -c1-200 | head -45; } >> $S
done
echo "i2 done: $*"
