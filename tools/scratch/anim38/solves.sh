#!/bin/sh
# solve.py runs from an args file (one per line), in parallel. Usage: solves.sh <tag> <argsfile>
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/43e8c2e6-36a3-4fd7-8ca4-39c475e24666/scratchpad/a38
O=$S/s_$1
mkdir -p $O
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d/tools/anim
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
n=0
while IFS= read -r args; do
  [ -z "$args" ] && continue
  n=$((n+1))
  (echo "ARGS: $args"; eval python $S/solve.py $args --out $O/$n.json) > $O/$n.txt 2>&1 &
done < "$2"
wait
for f in $O/*.txt; do echo "== $(basename $f)"; head -1 $f; grep -E "^cycle|frames,|Error|error" $f | cut -c1-330; done
