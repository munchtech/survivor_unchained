#!/bin/bash
# Pad-navigation checks: each screen opened, a simulated pad pressing keys, a picture.
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/shot.sh
P=$1
bash $S ${P}_inv_pad 4.5 --quick warden --zone waystation --open inventory --pad --keys Right,Right,Up
bash $S ${P}_shop_pad 4.5 --quick warden --zone waystation --open shop:harlan --pad --keys Down,Right,Right
bash $S ${P}_talk_pad 5 --quick warden --zone waystation --open talk:rook --pad --keys Confirm,Down,Down
bash $S ${P}_draft_pad 5 --quick reaver --zone arena --open draft --pad --keys Right
bash $S ${P}_journal_pad 4.5 --quick warden --zone waystation --open journal --pad --keys SubNext,Down
bash $S ${P}_character 4 --quick warden --zone waystation --open character
bash $S ${P}_arts_pad 4.5 --quick warden --zone waystation --open arts --pad --keys Down,Down
bash $S ${P}_map_pad 5 --quick warden --zone verge --open map --pad --keys SubNext,Left
bash $S ${P}_pause_pad 4.5 --quick warden --zone waystation --open pause --pad --keys Down,Down
bash $S ${P}_table 4 --quick warden --zone waystation --open maps
bash $S ${P}_rest 4 --quick warden --zone waystation --open rest
bash $S ${P}_stash_pad 4.5 --quick warden --zone waystation --open stash --pad --keys Right
bash $S ${P}_result 7 --quick reaver --zone arena --open result
bash $S ${P}_chapter 4 --quick warden --zone waystation --open chapter
echo BATCH DONE
