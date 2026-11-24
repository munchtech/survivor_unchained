#!/usr/bin/env bash
# The 4.7.2 look match: take s01 on 4.7.2 only with --look47 numbers, each against the 4.5.1 clip look_ab.sh shot.
# usage: look_sweep.sh TAG:LOOK47[:off] ...   (":off" = glow off, compared with look_g45_glow; else with look_g45_base)
#   e.g. look_sweep.sh t1:con=1.2,white=64:off g1:con=1.2,white=64,glow=5
# out: godot/.shots/look_g47_<TAG>/s01/clip.mp4, frames + numbers in godot/.shots/godot47up/sw_<TAG>/, log look_sweep.log
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
G47=/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
O=$WT/godot/.shots/godot47up; mkdir -p $O; L=$O/look_sweep.log
cd $WT
for spec in "$@"; do
  IFS=: read tag look off <<< "$spec"
  ref=base; pf=""; [ "$off" = off ] && { ref=glow; pf="--perf-off glow"; }
  lk=""; [ -n "$look" ] && [ "$look" != - ] && lk="--look47 $look"
  GODOT="$G47" MOVES_OUT="look_g47_$tag" TURN_LABEL="godot47-up2: look sweep $tag" MOVES_FLAGS="--perf look --perf-warm 0 --perf-for 900 $pf $lk" \
    python tools/motion/move_baseline.py s01 > $O/sw_$tag.out 2>&1
  echo "[$(date +%T)] $tag ($look $off): $(grep -E '^s01:' $O/sw_$tag.out | head -1)" >> $L
  python tools/scratch/godot47/compare.py godot/.shots/look_g45_$ref/s01/clip.mp4 godot/.shots/look_g47_$tag/s01/clip.mp4 $O/sw_$tag 0.5,2.5 >> $L 2>&1
done
echo "[$(date +%T)] done $*" >> $L
