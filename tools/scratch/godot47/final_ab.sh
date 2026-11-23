#!/usr/bin/env bash
# Upgrade session 2: the final A/B on the same code. All 17 --moves12 takes on 4.5.1 (csproj re-pinned, restored after) and
# on 4.7.2; their tables; the look numbers on take s01 (glow on / off, as look_ab.sh); the judge's 1:1 frame pairs.
# MUST run before the Upgrade Project Files commit (4.5.1 reads this tree). Run through tools/quiet.py.
# out: godot/.shots/moves12_<g45s2|g47s2>/, godot/.shots/godot47up/{final_ab.log, TABLE_*s2.md, fin_*/, judge/}
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
G45=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
G47=/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
O=$WT/godot/.shots/godot47up; L=$O/final_ab.log; cd $WT
say() { echo "[$(date +%T)] $*" >> $L; }
holders() { python tools/turn.py show | grep '^godot' ; }
say "start; $(holders)"
LOOK="--perf look --perf-warm 0 --perf-for 900"
sed -i 's#Godot.NET.Sdk/4.7.2#Godot.NET.Sdk/4.5.1#' godot/SurvivorUnchained.csproj
sed -i 's#SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent }#Sync = true }#' godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/fin_build45.log 2>&1; say "build 4.5.1: $(grep -c 'error CS' $O/fin_build45.log) errors"
GODOT="$G45" MOVES_OUT=moves12_g45s2 TURN_LABEL="godot47-up2: moves12 4.5.1" python tools/motion/move_baseline.py all > $O/fin_moves45.out 2>&1
say "4.5.1 takes: $(grep -c 'exit 0' $O/fin_moves45.out) ok of $(grep -c '^s\|^p' $O/fin_moves45.out)"
for s in base glow; do off=""; [ $s = glow ] && off="--perf-off glow"
  GODOT="$G45" MOVES_OUT="fin_g45_$s" TURN_LABEL="godot47-up2: look 4.5.1 $s" MOVES_FLAGS="$LOOK $off" python tools/motion/move_baseline.py s01 > $O/fin_look45_$s.out 2>&1; done
git checkout -- godot/SurvivorUnchained.csproj godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/fin_build47.log 2>&1; say "build 4.7.2: $(grep -c 'error CS' $O/fin_build47.log) errors"
GODOT="$G47" MOVES_OUT=moves12_g47s2 TURN_LABEL="godot47-up2: moves12 4.7.2" python tools/motion/move_baseline.py all > $O/fin_moves47.out 2>&1
say "4.7.2 takes: $(grep -c 'exit 0' $O/fin_moves47.out) ok of $(grep -c '^s\|^p' $O/fin_moves47.out)"
for s in base glow; do off=""; [ $s = glow ] && off="--perf-off glow"
  GODOT="$G47" MOVES_OUT="fin_g47_$s" TURN_LABEL="godot47-up2: look 4.7.2 $s" MOVES_FLAGS="$LOOK $off" python tools/motion/move_baseline.py s01 > $O/fin_look47_$s.out 2>&1; done
MOVES_OUT=moves12_g45s2 python tools/motion/move_baseline_table.py $O/TABLE_g45s2.md > /dev/null 2>&1
MOVES_OUT=moves12_g47s2 python tools/motion/move_baseline_table.py $O/TABLE_g47s2.md > /dev/null 2>&1
say "tables: $(diff $O/TABLE_g45s2.md $O/TABLE_g47s2.md | grep -c '^[<>]') differing lines of $(wc -l < $O/TABLE_g45s2.md)"
for s in base glow; do
  python tools/scratch/godot47/compare.py godot/.shots/fin_g45_$s/s01/clip.mp4 godot/.shots/fin_g47_$s/s01/clip.mp4 $O/fin_$s 0.5,2.5 >> $L 2>&1
  for t in 0.5 2.5; do python tools/scratch/godot47/tone_fit.py curve $O/fin_$s/a_$t.png $O/fin_$s/b_$t.png >> $L 2>&1; done
done
for t in 0.5 2.5; do python tools/scratch/godot47/tone_fit.py glow $O/fin_base/a_$t.png $O/fin_glow/a_$t.png $O/fin_base/b_$t.png $O/fin_glow/b_$t.png >> $L 2>&1; done
# the judge's pairs: plain game frames (no perf harness) from the moves12 clips, both engines, same second
for spec in s01:0.5,3.0 s12d:0.5,2.0,3.5 s10a:1.5,2.5 s06:2.0 s13:2.0; do IFS=: read tk secs <<< "$spec"
  python tools/scratch/godot47/compare.py godot/.shots/moves12_g45s2/$tk/clip.mp4 godot/.shots/moves12_g47s2/$tk/clip.mp4 $O/judge/$tk $secs >> $L 2>&1
done
say "done; $(holders)"
