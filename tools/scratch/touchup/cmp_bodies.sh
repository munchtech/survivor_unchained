#!/bin/bash
# Throat: C01 s3 with each body swapped in (now, before the neck fix, before the body build). Holds ONE godot turn.
# bash cmp_bodies.sh <glbdir> tag1 tag2 ...   (expects <glbdir>/b_<tag>.glb). Restores heroine.glb from git after.
W=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1941eef2c79c45fe
GD="C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"
D=$1; shift
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "touchup: throat bodies" --wait 3600 --stale-ok || exit 1
for t in "$@"; do
  cp "$D/b_$t.glb" $W/godot/art/people/heroine.glb
  "$GD" --headless --path $W/godot --import > $D/import_$t.log 2>&1
  echo "[{\"name\": \"th_$t\", \"cine\": \"c01\", \"until\": 12, \"args\": [\"--stills\", \"3\"], \"keep\": [\"_s3_\"]}]" > $D/runs_$t.json
  python $W/tools/scratch/touchup/shoot.py $D/runs_$t.json --noturn
done
git -C $W checkout -- godot/art/people/heroine.glb
"$GD" --headless --path $W/godot --import > $D/import_restore.log 2>&1
python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py give godot "touchup: throat bodies"
echo ALLDONE
