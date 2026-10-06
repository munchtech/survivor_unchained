#!/bin/bash
# The full legal motion check (all four outfits), into motion8/, then the counts.
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
mkdir -p "$L/motion8"
OUT=motion8 PHASE=all ONLY="${ONLY:-warden arcanist ranger reaver}" bash "$L/motion3.sh" > "$L/motion8_run.log" 2>&1
python "$L/count.py" "$L/motion8" 6 > "$L/motion8_counts.txt" 2>&1
echo FULLDONE
