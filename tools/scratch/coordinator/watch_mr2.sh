#!/bin/bash
# Exits (one notification) when a live lead's handoff top shows MR READY (H6/H7/H8/S1), GATE G1 READY (look-l1), GATE READY (body-p1), PROPOSAL READY (story-s1) or a HANDOFF READY.
M=/c/Users/munch/Desktop/survivorsunchained
cd "$M"
SEEN="$M/.claude/worktrees/watch_seen.txt"; touch "$SEEN"
chk() { grep -v -E "@COMMIT|@<commit>|@<sha>|READY line|never rename" | grep -q -E "$1@[0-9a-f]{7,}|$1 [a-z_/.]+ on ${1##* }@[0-9a-f]{7,}"; }
while true; do
  for trip in combat-h6:combat:"MR READY" flare-h7:flare:"MR READY" seams-h8:experience:"MR READY" look-l1:art_style:"GATE G1 READY" body-p1:body:"GATE READY" combat-h6:combat:"HANDOFF READY" flare-h7:flare:"HANDOFF READY" seams-h8:experience:"HANDOFF READY" body-p1:body:"HANDOFF READY" story-s1:story:"MR READY" story-s1:story:"HANDOFF READY" story-s1:story:"PROPOSAL READY"; do
    b=${trip%%:*}; r=${trip#*:}; h=${r%%:*}; k=${r#*:}
    f="$M/.claude/worktrees/$b/docs/handoff/$h.md"
    hit=""
    [ -f "$f" ] && head -15 "$f" | grep "$k" | chk "$k $b" && hit="worktree file"
    git show "$b:docs/handoff/$h.md" 2>/dev/null | head -15 | grep "$k" | chk "$k $b" && hit="${hit:+$hit+}branch"
    if [ -n "$hit" ]; then
      line=$( (head -15 "$f" 2>/dev/null; git show "$b:docs/handoff/$h.md" 2>/dev/null | head -15) | grep -o -E "$k[: ]+[a-z_/.]*[ on]*$b@[0-9a-f]{7,}" | head -1)
      grep -qF "$line" "$SEEN" && continue
      echo "$line" >> "$SEEN"
      echo "$k: $b ($hit) at $(git log --oneline -1 "$b")"
      head -15 "$f" 2>/dev/null | grep -E "$k $b@[0-9a-f]{7,}" | head -2
      exit 0
    fi
  done
  sleep 90
done
