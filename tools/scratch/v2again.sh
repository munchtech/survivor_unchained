#!/bin/bash
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/shot.sh
bash $S v2_map 7 --quick warden --zone waystation --open map
bash $S v2_pack 6 --quick warden --zone waystation --items chain_shirt:2,iron_helm:1,silver_ring:3,wolfhide_cloak:4,bone_charm:1,wolf_pelt,bitterroot,stream_sample,manual_blink --open inventory --pad --keys Right,Right
bash $S v2_self 6 --quick warden --zone waystation --xp 900 --items chain_shirt:2,iron_helm:1 --open character --pad --keys Right
bash $S v2_map_verge 8 --quick warden --zone verge --time day --open map
