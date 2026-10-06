#!/bin/bash
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/shot.sh
P=$1
bash $S ${P}_title_pad 4 --pad --keys Down,Down
bash $S ${P}_create_pad 6 --new --pad --keys Down,Confirm,Confirm
bash $S ${P}_create_name 6 --new --keys TabNext,TabNext,TabNext
bash $S ${P}_prologue 12 --quick warden
bash $S ${P}_arena 16 --quick reaver --zone arena --auto idle
bash $S ${P}_verge_night 7 --quick arcanist --zone verge --time night
bash $S ${P}_inv_pad 5 --quick warden --zone waystation --open inventory --pad --keys Right,Down
echo BATCH DONE
