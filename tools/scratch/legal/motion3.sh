#!/bin/bash
# The legal motion check, part two: her other clips for each outfit with jiggle on, so the
# survey's "no exposed nipples or genitals in play" can be shown true (brief issue 2).
# motioncheck2.gd = lookdev + her clip library + SPREAD (frames over one pass of a looped
# clip) + VIEWS (several cameras a run) + FOLLOW (cameras keep with her hips).
#   PHASE=cup    the warden's left cup in the sprint, first (the open finding)
#   PHASE=all    every clip below for ONLY (default: all four outfits)
# Run from anywhere; it works in the main checkout's godot/. Pictures go to the scratchpad.
# Never run it while that checkout is importing: check for a "--import" Godot first.
set -u
cd /c/Users/munch/Desktop/survivorsunchained/godot || exit 1
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
S="$L/${OUT:-motion4}"
mkdir -p "$S"
STAND="chest:0,1.45,1.3,1.30:35;left:45,1.40,1.2,1.28:36;side:90,1.30,1.3,1.25:38;below:0,0.95,1.2,1.25:42"
FLOOR="low:0,0.55,1.9,0.25:45;lowside:90,0.55,1.9,0.25:45;top:25,2.0,1.4,0.25:50"
shoot() { # outfit clip views follow frames
  local o="$1" clip="$2" views="$3" follow="$4" frames="$5"
  env FOV=38 OUTFIT="$o" HAIR=ponytail SPREAD=1 MARKS=1 FRAMES="$frames" VIEWS="$views" FOLLOW="$follow" \
    timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$L/motioncheck2.gd" -- "her/$clip" "$S/${o}_${clip}.png" \
    </dev/null >"$S/log_${o}_${clip}.txt" 2>&1
  echo "$o $clip $(ls "$S" | grep -c "^${o}_${clip}_")"
}
# PHASE=calib: no outfit, one frame, to see that the marks sit where they should and that the
# counter finds them. These pictures show her bare: scratchpad only, never shown or published.
if [ "${PHASE:-all}" = calib ]; then
  mkdir -p "$L/calib"
  env FOV=38 HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=1 VIEWS="chest:0,1.45,1.3,1.30:35;below:0,0.95,1.2,1.25:42;side:90,1.30,1.3,1.25:38" \
    timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$L/motioncheck2.gd" -- "her/idle_warden" "$L/calib/calib.png" \
    </dev/null >"$L/calib/log.txt" 2>&1
  grep -E "legal marks|ERROR|SCRIPT" "$L/calib/log.txt" | head -20
  echo CALIBDONE
  exit 0
fi
if [ "${PHASE:-all}" = cup ]; then
  shoot warden sprint_warden "$STAND" "" 16
  echo CUPDONE
  exit 0
fi
COMBAT="sword_back sword_fore sword_heavy axe_back axe_fore axe_heavy axes_left axes_right axes_heavy daggers_back daggers_fore daggers_heavy chain_strike cast_bolt cast_flick cast_raise crossbow_shoot throw warcry hit nod exhale shiver catch_breath reach_coals"
TRAVEL="dash leap vault vault_back bull_rush chain_haul"
LOW="death death_back get_up lie_side_wake sit_log sit_back_heels"
for o in ${ONLY:-warden arcanist ranger reaver}; do
  case $o in ranger) c=stalker;; *) c=$o;; esac
  OWN="idle_$c idle_${c}_break ${c}_show stop_${c}_l stop_${c}_r"
  case $c in reaver) OWN="$OWN run_reaver_axes sprint_reaver_axes";; stalker) OWN="$OWN run_stalker_daggers sprint_stalker_daggers";; arcanist) OWN="$OWN run_arcanist_wand sprint_arcanist_wand";; esac
  for clip in $OWN $COMBAT; do shoot "$o" "$clip" "$STAND" "" 10; done
  for clip in $TRAVEL; do shoot "$o" "$clip" "$STAND" 1 10; done
  for clip in $LOW; do shoot "$o" "$clip" "$FLOOR" 1 10; done
done
echo MOTIONDONE
