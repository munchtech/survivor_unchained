#!/bin/bash
# Body 19 carve r3: game frames (+ --dump-her) of a body, one godot turn.
#   BODY=<glb or git> OUT=<dir> [DUMP=1] [LIST=list.txt] bash shoot.sh
set -u
R=/c/Users/munch/Desktop/survivorsunchained; W=$R/.claude/worktrees/armor-7
C=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ee2b9848-690d-4b1a-8af0-4c7c5717800a/scratchpad/body23/loops
GE=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
TN="body23: r1a"; P=$W/godot/art/people; L=${LIST:-/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ee2b9848-690d-4b1a-8af0-4c7c5717800a/scratchpad/body20/shots3/list.txt}; OUT=$1; BODY=$2; DUMP=${DUMP:-0}
mkdir -p $OUT
imp(){ (cd $W/godot && timeout 1500 "$GE" --headless --path . --import > $OUT/import_$1.log 2>&1; echo "import $1 exit $?"); }
cd $R
out=$(python tools/turn.py take godot "$TN" --wait 3000 ${STALE:-} --root $W 2>&1); echo "$out" | tail -2
echo "$out" | grep -q "yours" || { echo "NO TURN"; exit 1; }
(cd $W/godot && dotnet build -v q 2>&1 | tail -1)
if [ "$BODY" != git ]; then cp $BODY $P/heroine.glb; touch $P/heroine.glb; imp body; fi
cd $W/godot
while IFS='|' read n res flags args; do
  [ -z "$n" ] && continue; case "$n" in \#*) continue;; esac
  rm -f .shots/$n.png
  dd=""; [ "$DUMP" = 1 ] && dd="--dump-her $OUT/$n"
  timeout 500 "$GE" --path . --fixed-fps 60 --resolution $res $flags -- $args --shot $n --count 1 $dd </dev/null >"$OUT/log_$n.txt" 2>&1
  [ -f .shots/$n.png ] && mv .shots/$n.png $OUT/ && echo "$n: ok" || echo "$n: NO FRAME"
  grep -E "SCRIPT ERROR|Exception" "$OUT/log_$n.txt" | head -2
done < $L
cd $R
if [ "$BODY" != git ]; then (cd $W && git show HEAD:godot/art/people/heroine.glb > $P/heroine.glb); touch $P/heroine.glb; imp restore; fi
python tools/turn.py give godot "$TN" --root $W 2>&1 | tail -1
(cd $W && git status --short godot/art/people/heroine.glb; sha1sum godot/art/people/heroine.glb)
echo ALL DONE
