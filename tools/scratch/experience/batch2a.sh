#!/bin/sh
# One Godot turn: the early game as a new player meets it, and every new screen on the way.
# (experience director 2, 5 October: creation, the prologue's first minutes, the Waystation and its
# dial, the Verge by day and night with toasts and a tip, an arena and its result, loot and the first
# Legendary, a fall and a get-up, a loss and the morning at Chid's, the rest, pause, chapter, credits,
# the knee's choice.)
E=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/experience
F="--quick warden --sex female --log 10"
p() { name=$1; shift; python "$E/play.py" "$name" --timeout 900 -- "$@" | head -3; }
# The title, then creation's five steps, as she first meets them.
p n_title --seconds 5
for s in 0 1 2 3 4; do p n_create$s --new --sex female --step $s --seconds 5; done
# From the title on the autopilot: creation taken as it stands, then the prologue's first two minutes.
p n_prologue --auto --seconds 3 --every 4 --count 32
# The Waystation by day (walking), then the dial at dawn's end, dusk, nightfall and the night's nudge.
p n_way $F --zone waystation --clock 100 --auto --seconds 2 --every 3 --count 5
for c in 590 710 890 1070; do p n_dial$c $F --zone waystation --clock $c --auto idle --seconds 4 --count 1; done
# The Verge by day with a toast run and a tip as type on the world; then by night.
p n_vday $F --zone verge --clock 200 --auto --toasts 4 --tip 9 --seconds 3 --every 1.5 --count 12
p n_vnight $F --zone verge --clock 760 --auto --seconds 3 --every 4 --count 8
# A table arena, its first five minutes; then a won arena's result.
p n_arena $F --zone arena --auto --seconds 10 --every 15 --count 20
p n_arres $F --zone arena --open result --seconds 4 --every 3 --count 2
# A map: its drops landing (every tier) as she walks over them; the first Legendary's moment; its result.
p n_loot $F --zone map --tier 1 --people dead --auto --loot --seconds 2 --every 0.8 --count 16
p n_legend $F --zone map --tier 1 --people dead --auto --loot legendary --loot-at 3 --seconds 3 --every 0.4 --count 30
p n_mapres $F --zone map --tier 1 --people dead --open mapresult --seconds 4 --count 1
# Felled at the Hollow's boss: the fall's choices and the get-up; then let go: the morning at Chid's.
p n_rise $F --night hollow --stage 3 --auto idle --die 10 --choose rise --seconds 9 --every 0.5 --count 36
p n_loss $F --night hollow --stage 3 --auto idle --die 10 --choose letgo --seconds 9 --every 1.5 --count 30
# The rest at night (the lamp's choices, then the morning), pause, the chapter, the credits.
p n_rest $F --zone waystation --clock 890 --gold 60 --open rest --keys Pick1 --seconds 1.5 --every 1.5 --count 10
p n_menus $F --zone waystation --clock 100 --open pause,chapter,credits --every 3 --seconds 2 --count 3
# Greymuzzle at his knee: the choice from anywhere, and the camera's lean toward him.
p n_knee $F --night roost --stage 3 --bosshp 0.3 --auto --knee spare --on boss --seconds 4 --every 2 --count 40 --until 120
