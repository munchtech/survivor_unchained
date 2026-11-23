#!/usr/bin/env bash
# The 4.7.2 upgrade, item 2 evidence: the fx warm-up's pipelines by kind and its worst frame on both engines, from the editor
# (Debug C#, no shader baker), same code, twice each (the second with the caches warm). 4.5.1 runs with the csproj re-pinned
# (as keep_ab.sh), restored after. usage: kinds_ab.sh   (log: godot/.shots/godot47up/kinds_ab.log)
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
G45=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
G47=/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
T=C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
O=$WT/godot/.shots/godot47up; mkdir -p $O; L=$O/kinds_ab.log
cd $WT
leg() {  # exe tag
  until python $T take godot "godot47-up: kinds $2" --wait 20 --stale-ok >/dev/null; do sleep 10; done
  timeout 90 "$1" --path godot --resolution 2560x1440 -- --quick warden --sex female --zone map --dungeon hollow --veteran 9 --move-new --move-ab > $O/kinds_$2.log 2>&1
  python $T give godot "godot47-up: kinds $2" >/dev/null
  echo "$2: $(grep 'fx warm-up' $O/kinds_$2.log | sed 's/.*stand-ins drawn/stand-ins drawn/' | cut -c1-330)" >> $L
}
echo "[$(date +%T)] start" >> $L
sed -i 's#Godot.NET.Sdk/4.7.2#Godot.NET.Sdk/4.5.1#' godot/SurvivorUnchained.csproj
sed -i 's#SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent }#Sync = true }#' godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/kinds_build45.log 2>&1; echo "build45 $(grep -c ' error ' $O/kinds_build45.log) errors" >> $L
leg $G45 g45a; leg $G45 g45b
git checkout -- godot/SurvivorUnchained.csproj godot/src/Actors/PlayerView.cs
dotnet build godot/SurvivorUnchained.csproj > $O/kinds_build47.log 2>&1; echo "build47 $(grep -c ' error ' $O/kinds_build47.log) errors" >> $L
leg $G47 g47a; leg $G47 g47b
echo "[$(date +%T)] done" >> $L
cat $L
