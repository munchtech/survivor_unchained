#!/bin/sh
# One Godot turn: the four story fights whole on the autopilot (a frame every 10 s, each boss move
# tagged), on combat's tuned build: length, danger, the lean toward the boss, the knee, the growth.
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 10"
p() { name=$1; shift; python "$E/play.py" "$name" --timeout 1500 -- $F "$@" | head -3; }
p w_hollow --night hollow --auto --seconds 8 --every 10 --count 90 --on boss --until 900 --end
p w_roost --night roost --auto --knee finish --seconds 8 --every 10 --count 90 --on boss --until 900 --end
p w_dig --night dig --auto --seconds 8 --every 10 --count 90 --on boss --until 900 --end
p w_vault --night vault --auto --seconds 8 --every 10 --count 90 --on boss --until 900 --end
