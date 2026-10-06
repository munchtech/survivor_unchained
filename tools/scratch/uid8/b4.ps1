# Batch 4: fixes across creation, pause and its panels, rest, chapter; the man; the title.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid8'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot n0 7 --new --sex female
& $shot n1c 7 --new --sex female --step 1 --part 2
& $shot m0 8 --new --sex male
& $shot m1 8 --new --sex male --step 1
& $shot p0 6 --load $save --nocine --open pause
& $shot p1 7 --load $save --nocine --open pause --clicks "203:318"
& $shot p2 7 --load $save --nocine --open pause --clicks "211:358"
& $shot r0 6 --load $save --nocine --open rest
& $shot r1 9 --load $save --nocine --open rest --keys Pick1
& $shot ch 7 --load $save --nocine --open chapter
& $shot title 7
