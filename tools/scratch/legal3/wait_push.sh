#!/bin/bash
# Waits (up to N minutes) until the integration branch on origin moves past a given commit.
cd /c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af0973d59a5b2817a || exit 1
start=$(git rev-parse origin/claude/vigilant-galileo-l6jqyx)
end=$(( $(date +%s) + ${1:-9} * 60 ))
while [ "$(date +%s)" -lt "$end" ]; do
  git fetch -q origin claude/vigilant-galileo-l6jqyx 2>/dev/null
  now=$(git rev-parse FETCH_HEAD)
  if [ "$now" != "$start" ]; then git log --oneline "$start..$now" | head -8; exit 0; fi
  python -c "import time; time.sleep(30)"
done
echo "no push yet"
