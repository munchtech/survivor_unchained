#!/bin/bash
# Action-clip shots: B (--body p1) playing one of her clips whole-body through the --act harness (PlayerView.Act.cs).
# Usage: shoot.sh <regex on clip_cam>          e.g.  shoot.sh heroic_leap  |  shoot.sh 'iron_vow_close'  |  shoot.sh smoke
#        shoot.sh --clip NAME "<act flags>" [SECONDS] [CLOSE] [regex]     any clip of her library, e.g.
#        shoot.sh --clip run_warden "--act-at 1 --act-travel 4 --act-repeat 2" 8 0.45
# One godot run per clip and camera (<clip>_play, <clip>_close): PNG frames at 30 fps, 1920x1080, into M/<clip>/clips/<cam>/
# (the old f*.png there are removed), logs in M/<clip>/logs/<cam>.log. The CALLER takes the godot turn once for the batch.
# play = the game's play camera, untouched. close = --close-hold Z --act-rigid (the view carried with her root, no lag);
# Z is the game's closest zoom (0.45) where her whole figure stays in the frame, else the closest that holds her (Z table;
# found with `CLOSE=<z> NOMOVIE=1 ACT_M=<scratch> shoot.sh <clip>_close` then `sheets.py --box <clip>`: 0 frames out).
# Env: ACT_M (the output folder), NOMOVIE=1 (no frames written, logs only: zoom trials, measures), CLOSE=<z> (overrides Z).
M=${ACT_M:-/c/Users/munch/Desktop/survivorsunchained_inputs/motion_a1/stageB/actions}
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
cd "$(dirname "$0")/../../../godot" || exit 1
B="--body p1 --p1-probe --hair braid --nohud --open-eyes --time day --zone arena --quick warden --no-spawn --no-foes --lab --noannounce --no-banners"
# per clip: its act flags, its run seconds (act at 1.0 + the act + 1.5 s of settle), its close zoom
declare -A F SEC Z
F[heroic_leap]="--act-at 1.0 --act-travel 6";                  SEC[heroic_leap]=6;      Z[heroic_leap]=0.31
F[bladestorm_loop]="--act-at 1.0 --act-spin 2.25 --act-hold 2"; SEC[bladestorm_loop]=6;  Z[bladestorm_loop]=0.45
F[iron_vow]="--act-at 1.0 --act-hold 2";                        SEC[iron_vow]=6;         Z[iron_vow]=0.45
F[shield_charge]="--act-at 1.0 --act-travel 6";                 SEC[shield_charge]=6;    Z[shield_charge]=0.45
SMOKE=0
if [[ $1 == --clip ]]; then
  for k in "${!F[@]}"; do unset "F[$k]"; done
  F[$2]="$3"; SEC[$2]=${4:-6}; Z[$2]=${5:-0.45}; ONLY=${6:-.}
else
  ONLY=${1:-.}
  if [[ $ONLY == smoke ]]; then   # the harness proof on today's clips: walk at play, idle at close
    SMOKE=1; ONLY=.
    F[walk_warden]="--act-at 1 --act-travel 3 --act-repeat 2"; SEC[walk_warden]=7;  Z[walk_warden]=0.45
    F[idle_warden]="--act-at 1 --act-hold 2 --act-spin 0.5";   SEC[idle_warden]=10; Z[idle_warden]=0.45
  fi
fi
for clip in "${!F[@]}"; do
  for cam in play close; do
    k=${clip}_$cam; [[ $k =~ $ONLY ]] || continue
    if [[ $SMOKE == 1 ]]; then [[ $k == walk_warden_play || $k == idle_warden_close ]] || continue; fi
    C=""; [[ $cam == close ]] && C="--close-hold ${CLOSE:-${Z[$clip]}} --act-rigid"
    d=$M/$clip/clips/$cam; mkdir -p $d $M/$clip/logs
    MOV="--write-movie $d/f.png"; if [[ $NOMOVIE == 1 ]]; then MOV=""; else rm -f $d/f*.png; fi
    timeout 500 "$G" --path . --fixed-fps 30 --resolution 1920x1080 $MOV -- --shot a1_act_$k ${F[$clip]} --act $clip --facing 90 $C $B --seconds ${SEC[$clip]} > "$M/$clip/logs/$cam.log" 2>&1
    echo "== $k exit $? frames $(ls $d | wc -l)"; grep "act:" "$M/$clip/logs/$cam.log" | grep -v "act: scr f="
  done
done
echo SHOTS DONE
