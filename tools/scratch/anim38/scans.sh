#!/bin/sh
# seatscan.py in parallel, one process per dx. Usage: scans.sh <tag> <piece> <side> <start> "<dx list>" "<dy list>"
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/463a4243-9324-49b0-bda9-b9fb9a9d68b1/scratchpad/a38
O=$S/sc_$1; mkdir -p $O
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d/tools/anim
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for x in $5; do
  seats=""; for y in $6; do seats="$seats $x,$y"; done
  python $S/seatscan.py $2 $3 $4 $seats > $O/x$x.txt 2>&1 &
done
wait
cat $O/x*.txt | grep TOTAL | sort -t' ' -k2 -g | cut -c1-400
