#!/bin/bash
# Lane G item 3 (16 Nov): the owner's bare-shape gate, A|B nude by day at the 4 game cameras, 1:1 (1920x1080).
# A = the shipped body, B = --body p1 (published round_39d). Commands as gate2/shoot.sh (lead 6, 7-8 Nov). Raw frames in
# the worktree's git-ignored godot/.shots/bare_g/<A|B>/ (rule 6b). Takes and gives back the godot turn.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a8359f8b3c48d4eb8
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
TURN=/c/Users/munch/Desktop/survivorsunchained/tools/turn.py
O=$WT/godot/.shots/bare_g
C0="--hair braid --nohud --hide-slots all --open-eyes --no-pointer"
declare -A S
S[look_look_day]="--new --sex female --step 1 --archetype reaver --zoom 0.45 --time day --seconds 5"
S[close_town_day]="--zone waystation --quick reaver --close 1 --idle-after 1 --time day --seconds 5"
S[play_town_day]="--zone waystation --quick reaver --time day --seconds 5"
S[play_play_day]="--zone arena --quick reaver --auto idle --time day --seconds 5"
python $TURN take godot "lane G: bare-shape shots" --wait 90 || { echo "NO TURN"; exit 2; }
cd $WT/godot && dotnet build -v q -nologo > $O/build.log 2>&1 || { echo "BUILD FAILED"; python $TURN give godot "lane G: bare-shape shots"; exit 3; }
for BODY in A B; do
  mkdir -p $O/$BODY
  X="--body a"; [ $BODY = B ] && X="--body p1 --p1-probe"
  for k in look_look_day close_town_day play_town_day play_play_day; do
    timeout 400 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- --shot ${k} ${S[$k]} $C0 $X > $O/$BODY/$k.log 2>&1
    echo "== $BODY $k exit $?"; grep -E "saved|ERROR|Exception" $O/$BODY/$k.log | head -3
    f=$(grep -o "saved [^ ]*\.png" $O/$BODY/$k.log | head -1 | cut -d' ' -f2); [ -n "$f" ] && cp "$f" $O/$BODY/$k.png
  done
done
python $TURN give godot "lane G: bare-shape shots"
echo DONE
