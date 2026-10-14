#!/bin/bash
# Close-ups in the outfits lead's worktree: each line "outfit angle camz dist targetz fov name [targetx targetz]";
# out in $CU (default scratchpad hs/cu)/<name>.png. Run while holding a Godot turn
# (TURN=1 takes and gives one itself). POSE=<clip> for a pose other than Idle; EXTRA="K=V ..."
# passes more lookdev settings (FRAMES, NOJIGGLE= to turn jiggle on, and so on).
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"  # (this worktree)
S="${OSCR:?set OSCR, the outfits scratch folder}/hs"
T="python $WT/tools/turn.py"
# (take: --root this worktree, so the freshness gate checks it; exit 2 = stale art: stop, never spin)
take() { while :; do $T take "$1" "$W" --wait 60 --root "$WT" >/dev/null 2>&1; r=$?; [ $r -eq 0 ] && return 0; [ $r -eq 2 ] && { echo "STALE: $T take $1 --root $WT refused (merge integration / reimport)"; exit 2; }; done; }
W="outfits lead: close-ups"
[ -n "$TURN" ] && { take godot; }
cd $WT/godot
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
CU="${CU:-$S/cu}"; mkdir -p "$CU"
while read o a cz d tz f n tx tzz; do
  [ -z "$o" ] && continue
  case "$o" in \#*) continue;; esac
  env $EXTRA FOV=$f OUTFIT=$o HAIR=${HAIR:-ponytail} NOLIFE=1 NOJIGGLE=${NOJIGGLE-1} ORBIT=$a,$cz,$d,$tz${tx:+,$tx,${tzz:-0}} timeout 300 "$G" --path . --resolution ${RES:-1920x1080} -s res://tools_scenes/lookdev.gd -- "${POSE:-Idle}" "$CU/$n.png" </dev/null >"$CU/log_$n.txt" 2>&1
done < "${1:-/dev/stdin}"
[ -n "$TURN" ] && $T give godot "$W" >/dev/null
echo CLOSEUPSDONE
