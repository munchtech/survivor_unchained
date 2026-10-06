#!/bin/bash
# The after set: every screen, keyboard and mouse, and with a pad where focus matters.
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/shot.sh
P=after
I="chain_shirt:2,iron_helm:1,silver_ring:3,wolfhide_cloak:4,bone_charm:1,wolf_pelt,bitterroot,stream_sample,manual_blink"
bash $S ${P}_title 7
bash $S ${P}_title_pad 5 --pad --keys Down
bash $S ${P}_create 6 --new
bash $S ${P}_create_pad 6 --new --pad --keys Down,Confirm
bash $S ${P}_prologue 10 --quick warden
bash $S ${P}_town_day 7 --quick warden --zone waystation --time day
bash $S ${P}_verge_night 7 --quick arcanist --zone verge --time night
bash $S ${P}_arena 16 --quick reaver --zone arena --auto idle
bash $S ${P}_arena_edges 6 --quick reaver --zone arena --auto idle --horde 3:wolf! --dist 70 --spread 5
bash $S ${P}_draft 6 --quick reaver --zone arena --open draft
bash $S ${P}_draft_pad 6 --quick reaver --zone arena --open draft --pad --keys Right
bash $S ${P}_pack 5 --quick warden --zone waystation --items $I --open inventory
bash $S ${P}_pack_pad 6 --quick warden --zone waystation --items $I --open inventory --pad --keys Right,Right,Right
bash $S ${P}_self 5 --quick warden --zone waystation --xp 2000 --open character
bash $S ${P}_self_pad 6 --quick warden --zone waystation --xp 2000 --open character --pad --keys Down,Right,Down
bash $S ${P}_arts_pad 5 --quick warden --zone waystation --open arts --pad --keys Down
bash $S ${P}_journal 5 --quick warden --zone waystation --open journal
bash $S ${P}_people 8 --quick warden --zone waystation --open talk:rook --pad --keys Confirm,Cancel,Journal,SubNext
bash $S ${P}_map_town 6 --quick warden --zone waystation --open map
bash $S ${P}_map_pad 7 --quick warden --zone waystation --open map --pad --keys Down,Down,Down
bash $S ${P}_map_verge 6 --quick warden --zone verge --open map
bash $S ${P}_pause_pad 5 --quick warden --zone waystation --open pause --pad --keys Down
bash $S ${P}_rest 5 --quick warden --zone waystation --open rest
bash $S ${P}_stash 5 --quick warden --zone waystation --items $I --open stash
bash $S ${P}_shop 5 --quick warden --zone waystation --items $I --open shop:harlan
bash $S ${P}_shop_pad 6 --quick warden --zone waystation --items $I --open shop:harlan --pad --keys Right,Right
bash $S ${P}_table 5 --quick warden --zone waystation --open maps
bash $S ${P}_talk 6 --quick warden --zone waystation --open talk:rook
bash $S ${P}_talk_pad 7 --quick warden --zone waystation --open talk:rook --pad --keys Confirm,Down,Down,Confirm,Confirm
bash $S ${P}_prompt 4 --quick warden --zone waystation --at 19,4.5
bash $S ${P}_result 7 --quick reaver --zone arena --open result
bash $S ${P}_chapter 5 --quick warden --zone waystation --open chapter
echo BATCH DONE
