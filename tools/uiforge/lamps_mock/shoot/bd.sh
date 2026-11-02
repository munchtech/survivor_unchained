#!/bin/bash
# UI 25 backdrops: seed the import cache, build, import, then foot/no-foot pairs + today's board pages, one godot turn.
S="$(cd "$(dirname "$0")" && pwd)"   # UI 26: this script's own folder (was the coordinator's scratch folder)
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/ui-25
WW='C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25'
T=C:/Users/munch/Desktop/survivorsunchained/tools/turn.py
GODOT="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
cd "$S"; mkdir -p logs out
(cd $W && dotnet build godot/SurvivorUnchained.csproj -v q 2>&1 | tail -3)
python $T take godot "ui25: backdrops" --wait 3000 --root $W || { echo "TURN REFUSED"; exit 1; }
echo "import $(date +%T)"
timeout 1800 "$GODOT" --headless --path $W/godot --import > logs/import.log 2>&1
echo "import exit $?"
P='ember=0.6,draught=2,art=0.6,dash=2'
python shot.py u25_town_day_foot   --quick warden --zone waystation --time day --seconds 12 --hud-pin "$P"
python shot.py u25_town_day_nofoot --quick warden --zone waystation --time day --seconds 12 --hud-pin "$P" --no-foot
python shot.py u25_ford_night_foot   --quick warden --zone lowford --time night --seconds 7 --hud-pin "$P"
python shot.py u25_ford_night_nofoot --quick warden --zone lowford --time night --seconds 7 --hud-pin "$P" --no-foot
python shot.py u25_today_lamps --quick warden --zone waystation --time day --board --open arts --xp 3000 --keys SubNext,SubNext --seconds 10
python shot.py u25_today_wicks --quick warden --zone waystation --time day --board --open arts --xp 3000 --keys SubNext,SubNext,SubNext --seconds 10
python $T give godot "ui25: backdrops"
cp $W/godot/.shots/u25_*.png out/ 2>/dev/null
ls -la out
grep -i "error\|exception" logs/u25_*.log | grep -v "^\s*at \|RID\|RenderingServer\|never freed\|still in use" | sort | uniq -c | head -10
echo "DONE $(date +%T)"
