#!/bin/bash
# Prints each new commit on the integration branch (polled every minute), from the legal worktree.
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a || exit 1
base=$(git rev-parse origin/claude/vigilant-galileo-l6jqyx)
while true; do
  git fetch -q origin claude/vigilant-galileo-l6jqyx 2>/dev/null || true
  head=$(git rev-parse FETCH_HEAD)
  if [ "$head" != "$base" ]; then
    git log --oneline "$base..$head" | head -5
    base=$head
  fi
  sleep 60
done
