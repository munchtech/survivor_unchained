#!/bin/bash
# take the shared lock (retry every 60 s), shoot C3's 9 frames, release the lock even on failure
B23=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ee2b9848-690d-4b1a-8af0-4c7c5717800a/scratchpad/body23
for i in $(seq 1 90); do mkdir $B23/godot.lock 2>/dev/null && break; sleep 60; done
[ -d $B23/godot.lock ] || { echo "NO LOCK"; exit 1; }
trap 'rmdir $B23/godot.lock 2>/dev/null' EXIT
bash $B23/r1b/shoot.sh $B23/r1b/C3/shots "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ee2b9848-690d-4b1a-8af0-4c7c5717800a/scratchpad/body23/r1b/C3/heroine.glb"
