#!/bin/sh
# One Godot turn: the first pass of fixes, seen (the fall's hush, the knee's line and the lean, the
# roofs and crowns opened over her, the prompt over a person, the zone line's morning) and the map
# result's reveal at a frame a second.
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 10"
p() { name=$1; shift; python "$E/play.py" "$name" --timeout 900 -- $F "$@" | head -3; }
p v_fall --night hollow --stage 3 --auto idle --die 10 --choose rise --seconds 11.5 --every 0.5 --count 4
p v_wake --night hollow --stage 3 --auto idle --die 10 --choose letgo --seconds 26 --every 2 --count 8
p v_knee --night roost --stage 3 --bosshp 0.3 --auto --knee spare --seconds 4 --every 3 --count 40 --until 125
p v_way --zone waystation --clock 100 --auto --seconds 2 --every 3 --count 5
p v_chid --zone waystation --clock 100 --near chid --seconds 3 --count 1
p v_verge --zone verge --clock 400 --auto --seconds 3 --every 3 --count 6
p v_mapres --zone map --tier 1 --people dead --open mapresult --seconds 2 --every 1 --count 9
