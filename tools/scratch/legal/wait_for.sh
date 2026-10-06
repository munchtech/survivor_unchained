#!/bin/bash
# Waits until the full run's log shows a line starting with $1 (an outfit name) or the run ends.
L="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/legal"
until grep -q -E "^$1 |MOTIONDONE" "$L/motion8_run.log" 2>/dev/null; do sleep 5; done
tail -1 "$L/motion8_run.log"
