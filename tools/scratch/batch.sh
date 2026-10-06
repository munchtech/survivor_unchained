#!/bin/bash
# usage: batch.sh PREFIX  -- takes every screen in turn as PREFIX_<name>.png
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/shot.sh
P=$1
bash $S ${P}_title 7
bash $S ${P}_create 7 --new
bash $S ${P}_prologue 9 --quick warden
bash $S ${P}_town_day 7 --quick warden --zone waystation --time day
bash $S ${P}_verge_night 7 --quick arcanist --zone verge --time night
bash $S ${P}_arena 14 --quick reaver --zone arena --auto idle
bash $S ${P}_draft 5 --quick reaver --zone arena --open draft --every 1
bash $S ${P}_inventory 4 --quick warden --zone waystation --open inventory --every 1
bash $S ${P}_character 4 --quick warden --zone waystation --open character --every 1
bash $S ${P}_arts 4 --quick warden --zone waystation --open arts --every 1
bash $S ${P}_journal 4 --quick warden --zone waystation --open journal --every 1
bash $S ${P}_map 5 --quick warden --zone verge --open map --every 1
bash $S ${P}_pause 4 --quick warden --zone waystation --open pause --every 1
bash $S ${P}_rest 4 --quick warden --zone waystation --open rest --every 1
bash $S ${P}_stash 4 --quick warden --zone waystation --open stash --every 1
bash $S ${P}_shop 4 --quick warden --zone waystation --open shop:harlan --every 1
bash $S ${P}_table 4 --quick warden --zone waystation --open maps --every 1
bash $S ${P}_talk 5 --quick warden --zone waystation --open talk:rook --every 1
bash $S ${P}_chapter 4 --quick warden --zone waystation --open chapter --every 1
echo BATCH DONE
