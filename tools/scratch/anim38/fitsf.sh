#!/bin/sh
# fistfit runs from an args file (one per line), in parallel. Usage: fitsf.sh <tag> <argsfile>
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/463a4243-9324-49b0-bda9-b9fb9a9d68b1/scratchpad/a38
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
O=$S/f_$1
mkdir -p $O
cd $W; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
while IFS= read -r args; do
  [ -z "$args" ] && continue
  name=$(echo "$args" | tr -c 'a-zA-Z0-9_\n' '_' | cut -c1-70)
  (echo "ARGS: $args"; eval python tools/anim/fistfit.py $args) > $O/$name.txt 2>&1 &
done < "$2"
wait
for f in $O/*.txt; do echo "== $(basename $f)"; grep -E "seat y0|frames," $f | cut -c1-400; done
