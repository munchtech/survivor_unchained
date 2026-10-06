#!/bin/sh
# One Godot turn, everything this round needs: the story fights whole, the fall and rise, the
# dial, the tips and toasts as type, a map's drops and its result.
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 10"
p() { name=$1; shift; python "$E/play.py" "$name" --timeout 1500 -- $F "$@" | head -1; }
# The three story fights, whole, on the autopilot: a frame every 10 s and each boss move tagged.
p b1_roost --night roost --auto --seconds 8 --every 10 --count 90 --on boss --until 720
p b1_dig --night dig --auto --seconds 8 --every 10 --count 90 --on boss --until 720
p b1_hollow --night hollow --auto --seconds 8 --every 10 --count 90 --on boss --until 720
# Felled at the boss twice: the fall's two choices, the rise, then the loss.
p b1_fall --night hollow --stage 3 --auto --choose rise --die 12,40 --seconds 10 --every 0.5 --count 70
# The dial in the town at dawn's end, dusk, nightfall and the night's nudge (the sun's light, the tip).
for c in 590 710 890 1070; do p b1_dial$c --zone waystation --clock $c --auto idle --seconds 4 --count 1; done
# The Verge by day: the tips as type on the world, walking.
p b1_verge --zone verge --clock 200 --auto --seconds 3 --every 2 --count 10
# A map's drops (every tier) as she walks over them, the toasts as type; then its result.
p b1_loot --zone map --tier 1 --people dead --auto --loot --seconds 2 --every 0.8 --count 20
p b1_mapres --zone map --tier 1 --people dead --open mapresult --seconds 6 --every 3 --count 3
p b1_mapfell --zone map --tier 1 --people dead --open mapresult --fell --seconds 6 --count 1
