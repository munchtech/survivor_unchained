#!/bin/sh
# Skills' worst case for the crowd's status read: sh status_runs.sh TAG (frost and fire, 24 frames each).
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
A="--quick arcanist --zone arena --people dead --time night --tier 2 --lab --horde 70,8:risen! --dist 3 --spread 9 --seconds 2.5 --every 0.08 --count 24"
python "$E/play.py" "st_frost_$1" --timeout 300 -- $A --give hoarfrost:4 | head -1
python "$E/play.py" "st_fire_$1" --timeout 300 -- $A --give cinderfall:4 | head -1
