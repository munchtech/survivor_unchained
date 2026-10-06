#!/bin/bash
# usage: shots_all.sh PREFIX [filter]
S=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/uilead/shot.sh
P=$1; F=${2:-.}
ITEMS=chain_shirt:2,iron_helm:1,silver_ring:3,wolfhide_cloak:4,bone_charm:1,wolf_pelt,bitterroot,stream_sample,manual_blink
SAVES="$APPDATA/SurvivorUnchainedUiLead/saves"
STORY=/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/uilead/qasaves/roost_emptied.json
run() { n=$1; shift; if echo "$n" | grep -qE "$F"; then
  # Quick runs save over slot 0: the story save goes back before every --continue.
  if echo "$*" | grep -q -- "--continue"; then cp "$STORY" "$SAVES/slot0.json"; printf '{"last":0}' > "$SAVES/meta.json"; fi
  bash $S ${P}_$n "$@"; fi; }
run arena 16 --quick reaver --zone arena --auto idle
run hud_verge 8 --quick warden --zone verge --time day
run hud_town 6 --quick warden --zone waystation
run pack 6 --quick warden --zone waystation --items $ITEMS --open inventory
run pack_pad 6 --quick warden --zone waystation --items $ITEMS --open inventory --pad --keys Right,Right
run self 6 --quick warden --zone waystation --xp 900 --items chain_shirt:2,iron_helm:1 --open character
run self_pad 6 --quick warden --zone waystation --xp 900 --items chain_shirt:2,iron_helm:1 --open character --pad --keys Right
run map 7 --quick warden --zone waystation --open map
run map_verge 8 --quick warden --zone verge --time day --open map
run map_pad 7 --quick warden --zone waystation --open map --pad --keys Down,Down
run draft 6 --quick reaver --zone arena --open draft
run draft_pad 6 --quick reaver --zone arena --open draft --pad --keys Right
run talk 7 --quick warden --zone waystation --open talk:rook
run talk_pad 7 --quick warden --zone waystation --open talk:rook --pad --keys Down
run shop 7 --quick warden --zone waystation --items $ITEMS --open shop:harlan
run shop_pad 7 --quick warden --zone waystation --items $ITEMS --open shop:harlan --pad --keys Right,Right
run stash 7 --quick warden --zone waystation --items $ITEMS --open stash
run stash_pad 7 --quick warden --zone waystation --items $ITEMS --open stash --pad --keys Right
run create 8 --new
run create_pad 8 --new --pad --keys Down
run create_name 9 --new --keys TabNext,TabNext,TabNext
run title 5
run title_pad 5 --pad --keys Down
run result 8 --quick reaver --zone arena --open result
run result_pad 8 --quick reaver --zone arena --open result --pad --keys Down
run rest 5 --quick warden --zone waystation --open rest
run rest_pad 5 --quick warden --zone waystation --open rest --pad --keys Down
run table 5 --quick warden --zone waystation --open maps
run table_pad 5 --quick warden --zone waystation --open maps --pad --keys Right
run chapter 5 --quick warden --zone waystation --open chapter
run journal 10 --continue --open journal
run journal_pad 10 --continue --open journal --pad --keys Down
run journal_people 11 --continue --open journal --pad --keys SubNext,Down,Down
run arts 10 --continue --open arts
run arts_pad 10 --continue --open arts --pad --keys Right,Down
run skills 10 --continue --open arts --keys SubNext
run pause 10 --continue --open pause
run pause_pad 10 --continue --open pause --pad --keys Down
run pause_settings 10 --continue --open pause --pad --keys Down,Down,Confirm
