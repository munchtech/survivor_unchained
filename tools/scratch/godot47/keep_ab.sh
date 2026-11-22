#!/bin/bash
# The den perf trace with the opening's shader hold (--keep-shaders) on both engines: 4.7.2 as committed, then 4.5.1 with
# the SDK pin and the 4.6 SyncMode line put back for its build only (restored from git after), then the 4.7.2 build again.
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"; cd "$WT"
G45="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
G47="C:/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe"
TURN=C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
LOG="$WT/godot/.shots/godot47/keep_ab.log"
others() { echo "[$(date +%T)] running before $1:"; tasklist //FO CSV //NH | grep -iE '^"(godot|blender)' || echo "  none"; }
perf() {  # exe tag
  others "perf $2"
  python $TURN take godot "p1-godot47: perf $2" --wait 1800 --stale-ok
  GODOT="$1" python tools/perf/run.py den --tag "$2" --repeat 4 -- --keep-shaders
  python $TURN give godot "p1-godot47: perf $2"
}
{
printf '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="SurvivorUnchainedPerf"\n' > godot/override.cfg
perf "$G47" g47k
sed -i 's#Godot.NET.Sdk/4.7.2#Godot.NET.Sdk/4.5.1#' godot/SurvivorUnchained.csproj
sed -i 's#SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent }#Sync = true }#' godot/src/Actors/PlayerView.cs
(cd godot && dotnet build SurvivorUnchained.csproj -nologo -v q | tail -3)
perf "$G45" g45k
git checkout -- godot/SurvivorUnchained.csproj godot/src/Actors/PlayerView.cs
(cd godot && dotnet build SurvivorUnchained.csproj -nologo -v q | tail -3)
rm -f godot/override.cfg
echo "KEEP AB DONE"
} > "$LOG" 2>&1
