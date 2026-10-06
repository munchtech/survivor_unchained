# Batch 9: the notices (a long line under its title), the map's names set clear of each other; 1080 and 1440.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot toasts 5.6 --zone verge --nocine --toasts 1.5
& $shot map_town 6 --load $save --nocine --open map
$env:SHOT_RES = '2560x1440'
& $shot map_town_1440 6 --load $save --nocine --open map
