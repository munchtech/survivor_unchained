#!/bin/bash
# solver 15: get_up ponytail, 3 views x 2 outfits x (on = PONYRIDGE=1, off = today), 61 frames, HAIRCLEAR logged.
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
C=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-af8dbda3195e438e4/tools/anim/out/clips
O=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/1515c1de-1208-43e2-b6eb-5133e0d07e1c/scratchpad/face/pt1
GU="FRAMES=61 STEP=1 START=0 COLS=8 LOOK=neck_01 ZOOM=2.4 HAIRCLEAR=1 W=400 H=400 HAIR=ponytail"
$T take godot "face: pony" --wait 1800 >/dev/null 2>&1
cd $WT/godot
for od in ${ODS:-warden reaver}; do for vw in ${VWS:-bk rv r3}; do for sw in ${SWS:-on off}; do
  V=""; [ $vw = bk ] && V="OFF=-0.9,0.35,-1.1"; [ $vw = r3 ] && V="VIEW=rthree"
  X=""; [ $sw = on ] && X="PONYRIDGE=1"
  out=$O/${vw}_${od}_${sw}.png; t0=$(date +%s)
  env $GU OUTFIT=$od $V $X timeout 300 "$G" --path . --fixed-fps 30 --resolution 400x400 -s res://tools_scenes/anim_review.gd -- "$C/get_up.json" "$out" </dev/null >"${out%.png}.log" 2>&1
  echo "$(basename $out) $(( $(date +%s) - t0 ))s $(grep -c HAIRCLEAR ${out%.png}.log) clear"
done; done; done
$T give godot "face: pony" >/dev/null 2>&1
echo PT1 DONE
