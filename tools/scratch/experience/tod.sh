#!/bin/sh
# The Verge and the town at a time of day, side by side: sh tod.sh TAG TIME (after a build).
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
python "$E/play.py" "tod_v_$1" --timeout 300 -- --quick warden --sex female --zone verge --time "$2" --auto idle --seconds 4 | head -1
python "$E/play.py" "tod_t_$1" --timeout 300 -- --quick warden --sex female --zone waystation --time "$2" --auto idle --seconds 4 | head -1
cd "$E" && python tsheet.py "tod_$1.png" 2 960 "tod_v_$1" "tod_t_$1"
