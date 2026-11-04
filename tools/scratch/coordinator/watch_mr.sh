#!/bin/bash
# Exits (one notification) when any live lead's handoff top shows MR READY, on its branch or in its worktree.
M=/c/Users/munch/Desktop/survivorsunchained
cd "$M"
while true; do
  for pair in combat-h1:combat audio-h3:audio seams-h4:experience; do
    b=${pair%%:*}; h=${pair##*:}
    f="$M/.claude/worktrees/$b/docs/handoff/$h.md"
    hit=""
    [ -f "$f" ] && head -15 "$f" | grep -q "MR READY" && hit="worktree file"
    git show "$b:docs/handoff/$h.md" 2>/dev/null | head -15 | grep -q "MR READY" && hit="${hit:+$hit+}branch"
    if [ -n "$hit" ]; then
      echo "MR READY: $b ($hit) at $(git log --oneline -1 "$b")"
      head -15 "$f" 2>/dev/null | grep "MR READY" | head -2
      exit 0
    fi
  done
  sleep 90
done
