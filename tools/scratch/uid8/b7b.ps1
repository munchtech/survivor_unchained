# Batch 7b: the review set, the rest.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid8'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$poor = Join-Path $sp 'poor.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot p0 6 --load $save --nocine --open pause
& $shot p1 7 --load $save --nocine --open pause --clicks "203:318"
& $shot p2 7 --load $save --nocine --open pause --clicks "211:358"
& $shot r0 6 --load $save --nocine --open rest
& $shot rpoor 6 --load $poor --nocine --open rest
& $shot r1 9 --load $save --nocine --open rest --keys Pick1
& $shot ch 8 --load $save --nocine --open chapter
& $shot cr 6 --load $save --nocine --open credits
& $shot ts 7 --panel settings
& $shot tl 7 --panel load
& $shot adults 6 --adults
