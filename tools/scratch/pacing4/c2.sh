#!/usr/bin/env bash
# frame-pacing-4 chain 2: start checks of one export with and without the early (out-of-view) warm-up phase.
# usage: c2.sh <export name under this worktree's release/godot> <tag>:<kind>...   kinds: pre (as built), nopre (--no-fx-pre)
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
X=$WT/release/godot/$1/SurvivorUnchained.exe; shift
GA="--quick warden --sex female --zone map --dungeon hollow --veteran 9 --move-new --move-ab"
Q=$WT/tools/scratch/pacing4/q.sh
for leg in "$@"; do
  tag="${leg%%:*}"; kind="${leg##*:}"
  case "$kind" in
    pre) bash $Q $tag 75 $X -- $GA ;;
    spre) SAMP_ALL=1 SAMPLER="$(basename $(dirname $X))\SurvivorUnchained.exe" SAMPLER_DELAY=0 SAMPLER_FOR=45 bash $Q $tag 110 $X -- $GA ;;
    nopre) bash $Q $tag 75 $X -- $GA --no-fx-pre ;;
  esac
  grep -a "fx pre-warm\|perf zone\|map built" $WT/godot/.shots/pacing4/$tag.log | cut -c1-400
done
