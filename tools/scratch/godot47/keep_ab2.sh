#!/bin/bash
# The den perf trace with the opening's shader hold (--keep-shaders), interleaved 4.7.2 / 4.5.1 legs (one recorded run each),
# so load from other sessions falls on both. Each leg logs every Godot/Blender running before and after it. 4.5.1's build
# re-pins the SDK and puts the 4.6 SyncMode line back as Sync (restored from git at the end).
#   bash tools/scratch/godot47/keep_ab2.sh ROUNDS
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"; cd "$WT"
G45="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
G47="C:/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe"
TURN=C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
LOG="$WT/godot/.shots/godot47/keep_ab2.log"
ROUNDS="${1:-3}"
procs() { echo "[$(date +%T)] $1: $(tasklist //FO CSV //NH | grep -iE '^"(godot|blender)' | cut -d, -f1,2 | tr '\n' ' ')"; }
use45() { sed -i 's#Godot.NET.Sdk/4.7.2#Godot.NET.Sdk/4.5.1#' godot/SurvivorUnchained.csproj
          sed -i 's#SyncMode = AnimationNodeBlendSpace2D.SyncModeEnum.Independent }#Sync = true }#' godot/src/Actors/PlayerView.cs
          (cd godot && dotnet build SurvivorUnchained.csproj -nologo -v q | grep -E " error |Error\(s\)"); }
use47() { git checkout -- godot/SurvivorUnchained.csproj godot/src/Actors/PlayerView.cs
          (cd godot && dotnet build SurvivorUnchained.csproj -nologo -v q | grep -E " error |Error\(s\)"); }
hold() {  # exe: the hold's own cost (the opening card's share), disk shader cache warm
  "$1" --path godot --resolution 1280x720 --audio-driver Dummy --quit-after 300 -- --quick warden --zone map --dungeon hollow --seed 1 --no-foes --keep-shaders 2>&1 | grep -E "^load:" | cut -c1-300; }
leg() {  # exe tag
  procs "before $2"
  GODOT="$1" python tools/perf/run.py den --tag "$2" -- --keep-shaders | grep -E "^ +(den_|run )"
  procs "after $2"
}
{
printf '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="SurvivorUnchainedPerf"\n' > godot/override.cfg
python $TURN take godot "p1-godot47: perf A/B" --wait 1800 --stale-ok
use47; echo "hold 4.7.2:"; hold "$G47"
use45; echo "hold 4.5.1:"; hold "$G45"
for r in $(seq 1 "$ROUNDS"); do
  use47; leg "$G47" "a47r$r"
  use45; leg "$G45" "a45r$r"
done
use47
python $TURN give godot "p1-godot47: perf A/B"
rm -f godot/override.cfg
echo "AB2 DONE"
} > "$LOG" 2>&1
