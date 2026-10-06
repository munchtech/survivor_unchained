#!/bin/sh
# Her blows critting in a crowd of champions at her elbow (they live long enough to be hit often): sh crit_runs.sh TAG
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
python "$E/play.py" "crit_$1" --timeout 300 -- --quick warden --sex female --zone arena --people dead --time night --tier 2 --lab --give "oathblade:4,cleaver:4,+precision:5" --horde "24:risen!" --dist 2 --spread 4 --seconds 1.5 --every 0.12 --count 24 | head -1
