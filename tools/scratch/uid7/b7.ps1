# Batch 7: notices (a long quest line set under its title), the kit switch, the Verge's map, a closed map.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot toasts 5.6 --zone verge --nocine --toasts 1.5
& $shot kit 6 --zone waystation --nocine --items iron_helm:3:of_the_long_chase@0 --nightkit iron_helm --open inventory
& $shot kit_night 6 --zone waystation --nocine --time night --items iron_helm:3:of_the_long_chase@0 --nightkit iron_helm --open inventory
& $shot map_verge 7 --zone verge --nocine --open map
& $shot mr_fell 11 --zone map --people dead --open mapresult --fell
