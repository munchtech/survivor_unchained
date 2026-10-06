# Batch 6: the chapter settled, the credits' seal, creation at 1440, the notice balanced.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid8'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot ch 8 --load $save --nocine --open chapter
& $shot cr 6 --load $save --nocine --open credits
& $shot adults 6 --adults
$env:SHOT_RES = '2560x1440'
& $shot n0_1440 7 --new --sex female
& $shot p0_1440 6 --load $save --nocine --open pause
& $shot r0_1440 6 --load $save --nocine --open rest
