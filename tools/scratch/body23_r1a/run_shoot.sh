#!/bin/bash
# take the shared Godot lock, shoot C1 and C2 (9 frames each), release the lock even on failure
H=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/ee2b9848-690d-4b1a-8af0-4c7c5717800a/scratchpad/body23
LOCK=$H/godot.lock
until mkdir $LOCK 2>/dev/null; do echo "lock busy $(date +%T)"; sleep 60; done
trap 'rmdir $LOCK 2>/dev/null; echo "lock released"' EXIT
echo "lock taken $(date +%T)"
for c in ${CANDS:-C1 C2}; do
  bash $H/r1a/shoot.sh "$H/r1a/$c/shots" "$H/r1a/$c/heroine.glb" > $H/r1a/$c/shoot.log 2>&1
  echo "$c: $(tail -3 $H/r1a/$c/shoot.log | tr '\n' ' ')"
done
