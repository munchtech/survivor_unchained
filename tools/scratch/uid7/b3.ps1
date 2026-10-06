# Batch 3: the results again (one named row, registers spaced), the fall and a loss in the Hollow,
# the Journal (an empty first day, and a second day's four sections), 1080 and 1440.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot mr_clear 11 --zone map --people dead --open mapresult
& $shot mr_many 11 --zone map --people dead --open mapresult --finds 17
& $shot ar_won 11 --zone arena --open result
& $shot ar_fell 11 --zone arena --open result --fell
& $shot jr_empty 6 --zone waystation --open journal
& $shot jr_quests 7 --load $save --open journal
& $shot jr_people 8 --load $save --open journal --keys SubNext
& $shot jr_deeds 8 --load $save --open journal --keys SubNext,SubNext
& $shot jr_codex 8 --load $save --open journal --keys SubNext,SubNext,SubNext
& $shot fall 30 --zone verge --night hollow --stage 3 --nocine --auto idle --die 10 --choose rise --until 32
& $shot loss 9.5 --zone verge --night hollow --stage 3 --nocine --auto idle --die 10 --choose letgo --every 0.6 --count 9 --until 50
$env:SHOT_RES = '2560x1440'
& $shot mr_clear_1440 11 --zone map --people dead --open mapresult
& $shot ar_won_1440 11 --zone arena --open result
& $shot jr_quests_1440 7 --load $save --open journal
