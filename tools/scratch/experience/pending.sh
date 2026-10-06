#!/bin/sh
# What each lead's branch holds that mine does not: sh pending.sh
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af2c026d86e1b532b || exit 1
for b in a63cd93fc73d5ed79 a435f4dd0ac80df75 a1d4562f44c7f6feb a26767f7f9955cb56 a69858664f1d3dd29 a7145e18b3eb78294 "$@"; do
  r=origin/worktree-agent-$b
  echo "== $b $(git log --oneline -1 $r)"
  echo "   ahead of mine: $(git rev-list --count HEAD..$r)"
  git log --oneline HEAD..$r --no-merges | head -8
done
