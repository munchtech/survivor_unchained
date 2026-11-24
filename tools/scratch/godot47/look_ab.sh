#!/usr/bin/env bash
# The 4.7.2 upgrade, item 3: which stage darkens the 4.7.2 frame. The deterministic 12-shot take s01 (frame-matched across
# engines) on both engines, as is and with glow / volumetric fog off (--perf-off), then the side by sides (compare.py).
# 4.5.1 runs with the csproj re-pinned (as keep_ab.sh), restored after.
# usage: look_ab.sh [take] [sets: comma list of "" glow volfog ...]   out: godot/.shots/look_<eng>_<set>/<take>/clip.mp4
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
G45=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
G47=/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
TAKE=${1:-s01}; SETS=${2:-base,glow,volfog}
O=$WT/godot/.shots/godot47up; mkdir -p $O; L=$O/look_ab.log
cd $WT
shoot() {  # exe eng
  for s in ${SETS//,/ }; do
    off=""; [ "$s" != base ] && off="--perf-off $s"
    GODOT="$1" MOVES_OUT="look_$2_$s" TURN_LABEL="godot47-up: look $2 $s" MOVES_FLAGS="--perf look --perf-warm 0 --perf-for 900 $off" \
      python tools/motion/move_baseline.py $TAKE > $O/look_$2_$s.out 2>&1
    echo "[$(date +%T)] $2 $s: $(grep -E "^$TAKE:" $O/look_$2_$s.out | head -1)" >> $L
  done
}
echo "[$(date +%T)] start $TAKE $SETS" >> $L
sed -i 's#Godot.NET.Sdk/4.7.2#Godot.NET.Sdk/4.5.1#' godot/SurvivorUnchained.csproj
sed -i 's#SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent }#Sync = true }#' godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/look_build45.log 2>&1
shoot $G45 g45
git checkout -- godot/SurvivorUnchained.csproj godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/look_build47.log 2>&1
shoot $G47 g47
for s in ${SETS//,/ }; do
  python tools/scratch/godot47/compare.py godot/.shots/look_g45_$s/$TAKE/clip.mp4 godot/.shots/look_g47_$s/$TAKE/clip.mp4 godot/.shots/godot47up/cmp_${TAKE}_$s 0.5,2.5 > $O/cmp_${TAKE}_$s.txt 2>&1
  echo "== $s" >> $L; cat $O/cmp_${TAKE}_$s.txt >> $L
done
echo "[$(date +%T)] done" >> $L
tail -30 $L
