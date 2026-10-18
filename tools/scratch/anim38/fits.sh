#!/bin/sh
# fistfit --fit runs in parallel, no write. Usage: fits.sh <tag> "<piece args>" ["<piece args>" ...]
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
O=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/463a4243-9324-49b0-bda9-b9fb9a9d68b1/scratchpad/a38/f_$1
shift
mkdir -p $O
cd $W; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
i=0
for args in "$@"; do
  i=$((i+1))
  name=$(echo "$args" | tr -c 'a-zA-Z0-9_\n' '_' | cut -c1-60)
  (echo "ARGS: $args"; eval python tools/anim/fistfit.py $args) > $O/$name.txt 2>&1 &
done
wait
for f in $O/*.txt; do echo "== $f"; grep -E "^seat|frames," $f; done
