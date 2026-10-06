#!/bin/sh
# Which commits have reached this branch: sh landed.sh SHA [SHA...]
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af2c026d86e1b532b || exit 1
for c in "$@"; do
  if git merge-base --is-ancestor "$c" HEAD; then echo "$c merged"; else echo "$c not merged"; fi
done
