#!/bin/bash
# The legal motion check: her clips for each outfit, with jiggle on, so the Steam survey's
# "no exposed nipples or genitals in play" can be shown true (docs/legal/LEGAL_BRIEF.md issue 2).
# Re-run after any outfit or body change, and before every upload.
#
#   tools/legal/motioncheck/run.sh calib      no outfit, one frame: are the marks where they should be?
#   tools/legal/motioncheck/run.sh tuckcalib  each outfit's pieces hidden: where its tucked skin lies
#   tools/legal/motioncheck/run.sh fp         each outfit without codes: count.py must find nothing
#   tools/legal/motioncheck/run.sh cup        the warden's sprint (the first finding)
#   tools/legal/motioncheck/run.sh all        every clip below for ONLY (default: all four outfits)
#
# Then: python tools/legal/motioncheck/count.py "$OUT" 6   (flags any frame showing a mark).
# GODOT: the Godot 4.5.1 .NET console binary. OUT: where pictures go, outside the repo by default.
# PROJECT: the imported godot folder to run in (default: this checkout's; a worktree has no import,
# so from a worktree pass the main checkout's, at the same commit).
# Run it in a checkout whose godot/.godot is imported, and never while that checkout imports.
# calib and tuckcalib pictures show her bare: never commit, share or publish them.
# Heavy work takes turns: python tools/turn.py take godot "legal: <job>" first, give it back after.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
G="${GODOT:-/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe}"
OUT="${OUT:-${TMPDIR:-/tmp}/legal_motion}"
mkdir -p "$OUT"
python "$ROOT/tools/legal/motioncheck/make_motioncheck.py" "$OUT/motioncheck.gd" >/dev/null || exit 1
cd "${PROJECT:-$ROOT/godot}" || exit 1
# (over: looking down into her neckline, as the play camera does from far above)
STAND="chest:0,1.45,1.3,1.30:35;left:45,1.40,1.2,1.28:36;side:90,1.30,1.3,1.25:38;below:0,0.95,1.2,1.25:42;over:15,2.20,0.65,1.30:38"
FLOOR="low:0,0.55,1.9,0.25:45;lowside:90,0.55,1.9,0.25:45;top:25,2.0,1.4,0.25:50"
shoot() { # outfit clip views follow frames
  local o="$1" clip="$2" views="$3" follow="$4" frames="$5"
  env FOV=38 OUTFIT="$o" HAIR=ponytail SPREAD=1 MARKS=1 FRAMES="$frames" VIEWS="$views" FOLLOW="$follow" \
    timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- "her/$clip" "$OUT/${o}_${clip}.png" \
    </dev/null >"$OUT/log_${o}_${clip}.txt" 2>&1
  echo "$o $clip $(ls "$OUT" | grep -c "^${o}_${clip}_.*png")"
}
case "${1:-all}" in
  calib)
    env FOV=38 HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=1 VIEWS="chest:0,1.45,1.3,1.30:35;below:0,0.95,1.2,1.25:42;side:90,1.30,1.3,1.25:38" \
      timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- "her/idle_warden" "$OUT/calib_idle.png" \
      </dev/null >"$OUT/log_calib.txt" 2>&1
    grep -E "legal marks" "$OUT/log_calib.txt"
    exit 0 ;;
  tuckcalib)
    # Each outfit's pieces hidden, its tuck kept: the cyan shows where its tucked skin lies and
    # how deep (paler is shallower). Shows her bare: scratchpad only.
    for o in ${ONLY:-warden arcanist ranger reaver}; do
      env FOV=38 OUTFIT="$o" LEGALBARE=1 HAIR=ponytail SPREAD=1 MARKS=1 FRAMES=1 VIEWS="chest:0,1.45,1.3,1.30:35;below:0,0.95,1.2,1.25:42;side:90,1.30,1.3,1.25:38;back:180,1.20,1.3,1.10:42" \
        timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- "her/idle_warden" "$OUT/tuck_${o}.png" \
        </dev/null >"$OUT/log_tuck_${o}.txt" 2>&1
    done
    exit 0 ;;
  cup)
    shoot warden sprint_warden "$STAND" "" 16
    exit 0 ;;
  fp)
    # Each outfit with the linear tonemapper and no codes: count.py must find nothing, or an
    # outfit's own colours could pass for a code.
    for o in warden arcanist ranger reaver; do
      env FOV=38 OUTFIT="$o" HAIR=ponytail SPREAD=1 LINEAR=1 FRAMES=4 VIEWS="$STAND" \
        timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- "her/sprint_warden" "$OUT/fp${o}_sprint.png" \
        </dev/null >"$OUT/log_fp_${o}.txt" 2>&1
    done
    exit 0 ;;
esac
COMBAT="sword_back sword_fore sword_heavy axe_back axe_fore axe_heavy axes_left axes_right axes_heavy daggers_back daggers_fore daggers_heavy chain_strike cast_bolt cast_flick cast_raise crossbow_shoot throw warcry hit nod exhale shiver catch_breath reach_coals"
TRAVEL="dash leap vault vault_back bull_rush chain_haul"
LOW="death death_back get_up lie_side_wake sit_log sit_back_heels"
for o in ${ONLY:-warden arcanist ranger reaver}; do
  case $o in ranger) c=stalker;; *) c=$o;; esac
  OWN="idle_$c idle_${c}_break ${c}_show stop_${c}_l stop_${c}_r run_$c sprint_$c"
  case $c in reaver) OWN="$OWN run_reaver_axes sprint_reaver_axes";; stalker) OWN="$OWN run_stalker_daggers sprint_stalker_daggers";; arcanist) OWN="$OWN run_arcanist_wand sprint_arcanist_wand";; esac
  for clip in $OWN $COMBAT; do shoot "$o" "$clip" "$STAND" "" 10; done
  for clip in $TRAVEL; do shoot "$o" "$clip" "$STAND" 1 10; done
  for clip in $LOW; do shoot "$o" "$clip" "$FLOOR" 1 10; done
done
echo MOTIONDONE
