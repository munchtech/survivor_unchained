#!/bin/bash
# After the Arcanist's run, the Stalker (ranger) and then the Reaver, each in its own turn.
L=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal3
python "$L/wait_for.py" file "$L/tuck1_arcanist.out" OUTFITDONE 120
for o in ranger reaver; do
  bash "$L/run_outfit.sh" "$o" tuck1 > "$L/tuck1_$o.out" 2>&1
done
echo CHAINDONE
