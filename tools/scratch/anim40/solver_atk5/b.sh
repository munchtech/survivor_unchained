#!/bin/bash
# b.sh CLIP [frames] [m5 args]: build one clip, print m5
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/anim-40
c=$1; fr=${2:-0-12}; shift; shift
python tools/anim/build.py --no-pack $c >/dev/null 2>&1 || echo BUILD FAIL
python tools/scratch/anim40/solver_atk5/m5.py $c --frames $fr "$@" | tail -n +2
