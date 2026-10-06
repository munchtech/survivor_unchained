#!/bin/bash
# The fix build (0e35921f): the finding clips, then the Stalker and the Reaver in full,
# each batch in its own Godot turn.
L=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3
bash "$L/findings.sh" fix1 > "$L/fix1_findings.out" 2>&1
for o in ranger reaver; do
  bash "$L/run_outfit.sh" "$o" fix1 > "$L/fix1_$o.out" 2>&1
done
echo FIXALLDONE
