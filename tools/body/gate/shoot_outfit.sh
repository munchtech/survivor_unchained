#!/bin/bash
# Lane G refit (16 Nov): A|B in a calling's outfit by day at the 4 game cameras + a run hold and a weapon hold at the play
# camera, 1:1 (1920x1080). A = the shipped body and A's outfit file; B = --body p1 (published round_39d) wearing its built gear
# (godot/art/gear/out/body_p1, P1Body.GearDir). Commands as shoot_g.sh (the bare-shape gate). Raw frames in the worktree's
# git-ignored godot/.shots/refit_b/<tag>/<A|B>/ (rule 6b). Takes the godot turn, imports, builds, shoots, gives it back.
# usage: shoot_outfit.sh CALLING [TAG] [BODIES] [KEYS]     CALLING = warden | reaver | arcanist | stalker (the ranger outfit)
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a8359f8b3c48d4eb8
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
TURN=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
CAL=${1:?calling}; TAG=${2:-$CAL}; BODIES=${3:-A B}
O=$WT/godot/.shots/refit_b/$TAG; mkdir -p $O
declare -A RUN=([warden]=run_warden [reaver]=run_reaver [arcanist]=run_arcanist [stalker]=run_stalker)
declare -A HIT=([warden]=sword_heavy@0.35 [reaver]=axe_heavy@0.35 [arcanist]=cast_bolt@0.3 [stalker]=daggers_heavy@0.2)
C0="--hair braid --nohud --open-eyes --no-pointer"
declare -A S
S[look_look_day]="--new --sex female --step 1 --archetype $CAL --zoom 0.45 --time day --seconds 5"
S[close_town_day]="--zone waystation --quick $CAL --close 1 --idle-after 1 --time day --seconds 5"
S[play_town_day]="--zone waystation --quick $CAL --time day --seconds 5"
S[play_play_day]="--zone arena --quick $CAL --auto idle --time day --seconds 5"
# (holds: at the town spawn; AT=x,z moves them, but 19,4.5 is a market stall with name labels (refit lead 1, 17 Nov))
AT=${AT:-}
S[play_run_hold]="--zone waystation ${AT:+--at $AT} --quick $CAL --time day --seconds 6 --facing 20 --hold ${RUN[$CAL]}@0.25"
S[play_hit_hold]="--zone waystation ${AT:+--at $AT} --quick $CAL --time day --seconds 6 --facing 30 --hold ${HIT[$CAL]}"
# (back views, the judge 17 Nov: her seat at the play camera, run away from the camera and the leap's crouch)
S[play_run_back]="--zone waystation ${AT:+--at $AT} --quick $CAL --time day --seconds 6 --facing 200 --hold ${RUN[$CAL]}@0.25"
S[play_leap_back]="--zone waystation ${AT:+--at $AT} --quick $CAL --time day --seconds 6 --facing 200 --hold leap@0.4"
KEYS=${4:-look_look_day close_town_day play_town_day play_play_day play_run_hold play_hit_hold}
python $TURN take godot "lane G refit: $TAG outfit shots" --wait 900 || { echo "NO TURN"; exit 2; }
give() { python $TURN give godot "lane G refit: $TAG outfit shots"; }
cd $WT/godot
timeout 900 "$G" --headless --path . --import > $O/import.log 2>&1; echo "import exit $?"
dotnet build -v q -nologo > $O/build.log 2>&1 || { echo "BUILD FAILED"; give; exit 3; }
for BODY in $BODIES; do
  mkdir -p $O/$BODY
  # (A wears the same calling rows as B: --standin 0, A's outfit file; the retired plate stand-ins are not compared)
  # (the Warden: A as the game ships her, wearing the plate_pauldrons_warden stand-in (main's call 17 Nov: B wears it too))
  X="--standin 0"; [ $CAL = warden ] && X=""; [ $BODY = B ] && X="--body p1 --p1-probe"
  for k in $KEYS; do
    timeout 400 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot rf_${TAG}_${BODY}_${k} ${S[$k]} $C0 $X </dev/null > $O/$BODY/$k.log 2>&1
    echo "== $BODY $k exit $?"; grep -aE "saved|ERROR|Exception" $O/$BODY/$k.log | head -3
    f=$(grep -ao "saved [^ ]*\.png" $O/$BODY/$k.log | head -1 | cut -d' ' -f2); [ -n "$f" ] && cp "$f" $O/$BODY/$k.png
  done
done
give
echo DONE
