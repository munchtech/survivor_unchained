#!/bin/bash
# Lane G flip gate (lead 6, 17 Nov): her on the DEFAULT body (godot/data/body/her_body.json, B = p1) against A (--body a),
# the Warden outfit, at the game cameras + the den + the hair styles, 1:1 (1920x1080). B runs pass NO --body flag, so the
# default path is what is shot. Also one check that a hidden calling (reaver) loads on A by default (the owner, 17 Nov:
# "hide all 3 besides warden for demo"). Raw frames in godot/.shots/refit_b/<tag>/<A|B>/ (rule 6b).
# usage: shoot_flip.sh [TAG] [BODIES] [KEYS]
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a8359f8b3c48d4eb8
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
TURN=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
TAG=${1:-flip1}; BODIES=${2:-A B}
O=$WT/godot/.shots/refit_b/$TAG; mkdir -p $O
C0="--nohud --open-eyes --no-pointer"
declare -A S
S[look_look_day]="--new --sex female --step 1 --archetype warden --zoom 0.45 --time day --seconds 5 --hair braid"
S[close_town_day]="--zone waystation --quick warden --close 1 --idle-after 1 --time day --seconds 5 --hair braid"
S[play_town_day]="--zone waystation --quick warden --time day --seconds 5 --hair braid"
S[play_play_day]="--zone arena --quick warden --auto idle --time day --seconds 5 --hair braid"
S[play_run_hold]="--zone waystation --quick warden --time day --seconds 6 --facing 20 --hold run_warden@0.25 --hair braid"
S[play_hit_hold]="--zone waystation --quick warden --time day --seconds 6 --facing 30 --hold sword_heavy@0.35 --hair braid"
S[play_run_back]="--zone waystation --quick warden --time day --seconds 6 --facing 200 --hold run_warden@0.25 --hair braid"
S[play_leap_back]="--zone waystation --quick warden --time day --seconds 6 --facing 200 --hold leap@0.4 --hair braid"
S[play_den]="--zone map --dungeon den --seed 11 --quick warden --time day --seconds 8 --hair braid"
S[look_ponytail]="--new --sex female --step 1 --archetype warden --zoom 0.45 --time day --seconds 5 --hair ponytail"
S[look_pixie]="--new --sex female --step 1 --archetype warden --zoom 0.45 --time day --seconds 5 --hair pixie"
S[close_ponytail]="--zone waystation --quick warden --close 1 --idle-after 1 --time day --seconds 5 --hair ponytail"
S[close_pixie]="--zone waystation --quick warden --close 1 --idle-after 1 --time day --seconds 5 --hair pixie"
S[hidden_reaver]="--zone waystation --quick reaver --time day --seconds 5 --hair braid"
KEYS=${3:-look_look_day close_town_day play_town_day play_play_day play_run_hold play_hit_hold play_run_back play_leap_back play_den look_ponytail look_pixie close_ponytail close_pixie hidden_reaver}
python $TURN take godot "lane G flip gate: $TAG" --wait 900 || { echo "NO TURN"; exit 2; }
give() { python $TURN give godot "lane G flip gate: $TAG"; }
cd $WT/godot
timeout 900 "$G" --headless --path . --import > $O/import.log 2>&1; echo "import exit $?"
dotnet build -v q -nologo > $O/build.log 2>&1 || { echo "BUILD FAILED"; give; exit 3; }
for BODY in $BODIES; do
  mkdir -p $O/$BODY
  X="--p1-probe"; [ $BODY = A ] && X="--body a"
  for k in $KEYS; do
    [ $BODY = A ] && [ $k = hidden_reaver ] && continue
    timeout 400 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot fl_${TAG}_${BODY}_${k} ${S[$k]} $C0 $X </dev/null > $O/$BODY/$k.log 2>&1
    echo "== $BODY $k exit $? p1-lines $(grep -ac '^p1:' $O/$BODY/$k.log)"; grep -aE "Exception" $O/$BODY/$k.log | head -2
    f=$(grep -ao "saved [^ ]*\.png" $O/$BODY/$k.log | head -1 | cut -d' ' -f2); [ -n "$f" ] && cp "$f" $O/$BODY/$k.png
  done
done
give
echo DONE
