# Batch 4: the Journal's sections (an empty first day; a second day's quests, people, deeds and codex),
# the fall's mirrored choices, a fallen night's result; 1080 and 1440.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot jr_empty 6 --zone waystation --nocine --open journal
& $shot jr_quests 7 --load $save --nocine --open journal
& $shot jr_people 7 --load $save --nocine --open journal --journal people
& $shot jr_deeds 7 --load $save --nocine --open journal --journal deeds
& $shot jr_codex 7 --load $save --nocine --open journal --journal codex
& $shot ar_fell 11 --zone arena --open result --fell
& $shot fall 30 --zone verge --night hollow --stage 3 --nocine --auto idle --die 10 --choose rise --until 32
$env:SHOT_RES = '2560x1440'
& $shot jr_quests_1440 7 --load $save --nocine --open journal
