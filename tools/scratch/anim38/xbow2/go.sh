#!/bin/sh
# go.sh clip [ev args]: ev + chest-frame path every 3rd frame
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a6b5a13d0be70144d
python tools/scratch/anim38/xbow2/ev.py "$@" 2>&1 | grep -v "^built\|^bodies"
python tools/scratch/anim38/xbow2/cpath.py $1 0:19:3 $(echo "$@" | grep -o -- "--hero")
