#!/usr/bin/env bash
# Upgrade session 2, judge round 2: takes s01 s11 s12 s10a on both engines at the same code, then the judge's 1:1 pairs
# (a = 4.5.1, b = 4.7.2) in godot/.shots/godot47up/judge2/. Must run before the Upgrade Project Files commit. Through tools/quiet.py.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
G45=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
G47=/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
O=$WT/godot/.shots/godot47up; L=$O/round2_ab.log; cd $WT; T=s01,s11,s12,s10a
sed -i 's#Godot.NET.Sdk/4.7.2#Godot.NET.Sdk/4.5.1#' godot/SurvivorUnchained.csproj
sed -i 's#SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent }#Sync = true }#' godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/r2_build45.log 2>&1; echo "build 4.5.1: $(grep -c 'error CS' $O/r2_build45.log) errors" >> $L
GODOT="$G45" MOVES_OUT=r2_g45 TURN_LABEL="godot47-up2: round 2 4.5.1" python tools/motion/move_baseline.py $T > $O/r2_45.out 2>&1
git checkout -- godot/SurvivorUnchained.csproj godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/r2_build47.log 2>&1; echo "build 4.7.2: $(grep -c 'error CS' $O/r2_build47.log) errors" >> $L
GODOT="$G47" MOVES_OUT=r2_g47 TURN_LABEL="godot47-up2: round 2 4.7.2" python tools/motion/move_baseline.py $T > $O/r2_47.out 2>&1
for spec in s01:0.5,3.0 s11:2.05,2.15,2.3 s12:1.35,1.8,2.3 s10a:2.05,2.15; do IFS=: read tk secs <<< "$spec"
  python tools/scratch/godot47/compare.py godot/.shots/r2_g45/$tk/clip.mp4 godot/.shots/r2_g47/$tk/clip.mp4 $O/judge2/$tk $secs >> $L 2>&1
done
echo "done $(grep -c 'exit 0' $O/r2_45.out)/$(grep -c 'exit 0' $O/r2_47.out) takes ok" >> $L
