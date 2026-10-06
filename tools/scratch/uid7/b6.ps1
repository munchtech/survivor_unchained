# Batch 6: the Map screen (the Waystation known, the Verge, a hover on a line), the Journal settled; 1080 and 1440.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot map_town 6 --load $save --nocine --open map
& $shot map_verge 7 --zone verge --nocine --open map
& $shot map_hover 7 --load $save --nocine --open map --clicks "h1400:330"
& $shot jr_quests 7 --load $save --nocine --open journal
$env:SHOT_RES = '2560x1440'
& $shot map_town_1440 6 --load $save --nocine --open map
