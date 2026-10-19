#!/bin/bash
# Merge a lead's branch into the integration branch in the main checkout.
#   bash tools/scratch/coordinator/merge_lead.sh <agent-id>
# Untracked .uid/.import files that the incoming branch tracks block a merge
# (Godot writes them on import); they are set aside first, not deleted.
set -e
M=/c/Users/munch/Desktop/survivorsunchained
b="$1"; git -C /c/Users/munch/Desktop/survivorsunchained rev-parse --verify -q "$b" >/dev/null || b="worktree-agent-$1"  # a branch name, or an agent id
cd "$M"
[ "$(git branch --show-current)" = "claude/vigilant-galileo-l6jqyx" ] || { echo "main checkout is not on the integration branch"; exit 1; }
B="$TEMP/hs/uid_backup/$(date +%s%N)"; mkdir -p "$B"
git ls-tree -r --name-only "$b" | grep -E "\.(uid|import)$" | while read -r f; do
  if [ -f "$f" ] && ! git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    mkdir -p "$B/$(dirname "$f")"; mv "$f" "$B/$f"
  fi
done
echo "merging $b ($(git log --oneline -1 "$b"))"
git merge --no-edit "$b" || { echo "CONFLICT: resolve, then git add and git commit --no-edit"; git diff --name-only --diff-filter=U; exit 2; }
# Legal gate: retired from merge requests 18 Oct (optional pre-store run only), so no --dry here.
echo "merged; now: cd godot/tests && dotnet test, then git push origin claude/vigilant-galileo-l6jqyx"
echo "if the lead's work is finished: powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/wt_remove.ps1 .claude/worktrees/agent-$1 (CLAUDE.md rule 1)"
