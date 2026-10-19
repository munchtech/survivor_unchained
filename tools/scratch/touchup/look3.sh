#!/bin/bash
# look.sh <outdir> <list> <hair> [cine-until] : Look/close-up stills from a list (name|who|args), optional C01 stills (s8, s8b, s10), one godot turn.
# list line: name|new:<archetype> or <calling>|extra args.  Env IMPORT=1 forces a reimport first.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe
G="/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
O=$1; L=$2; H=$3; U=$4; mkdir -p $O; cd $W/godot
if [ -n "$IMPORT" ]; then timeout 2400 "$G" --headless --path . --import >"$O/import.log" 2>&1 </dev/null; echo "import done"; fi
dotnet build SurvivorUnchained.csproj -v q >"$O/build.log" 2>&1 || { echo "BUILD FAILED"; exit 2; }
python $W/tools/turn.py take godot "touchup: look shots" --wait 3000 --root $W --stale-ok >/dev/null || { echo "NO TURN"; exit 1; }
while IFS='|' read n q ex; do
  [ -z "$n" ] && continue
  case "$q" in new:*) who="--new --archetype ${q#new:} --step 1";; *) who="--quick $q";; esac
  rm -f .shots/$n.png .shots/${n}_*.png
  timeout 300 "$G" --path . --fixed-fps 60 --resolution 1920x1080 -- $who --sex female --hair $H --nohud $ex --shot $n --seconds 6 --count 1 </dev/null >"$O/log_$n.txt" 2>&1
  f=$(ls .shots/$n*.png 2>/dev/null | head -1); if [ -n "$f" ]; then mv "$f" "$O/$n.png"; echo "$n ok"; else echo "$n MISSING"; fi
done < $L
if [ -n "$U" ]; then
  rm -f .shots/lkc_*
  timeout 900 "$G" --path . --resolution 1920x1080 -- --quick warden --sex female --zone lowford --nohud --cine c01 --shot lkc --until $U --preset own --skin fair --eyes moss --hair $H --stills 3 </dev/null >"$O/log_lkc.txt" 2>&1
  for f in .shots/lkc_*.png; do b=$(basename $f); if echo "$b" | grep -qE "_s3_|_s8_|_s8b_|_s10_|_s11_"; then mv "$f" "$O/$b"; else rm -f "$f"; fi; done
  echo "c01: $(ls $O/lkc_* 2>/dev/null | wc -l) png"
fi
python $W/tools/turn.py give godot "touchup: look shots" --root $W >/dev/null
echo LOOK_DONE
