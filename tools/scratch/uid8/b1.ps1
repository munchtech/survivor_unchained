# Batch 1 (before): creation's five steps, pause and its panels, rest and its morning, chapter, credits.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid8'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot c0 7 --new --sex female
& $shot c1 7 --new --sex female --step 1
& $shot c2 7 --new --sex female --step 2
& $shot c3 7 --new --sex female --step 3
& $shot c4 7 --new --sex female --step 4
& $shot p0 6 --load $save --nocine --open pause
& $shot p1 6 --load $save --nocine --open pause --clicks "150:367"
& $shot p2 6 --load $save --nocine --open pause --clicks "150:407"
& $shot r0 6 --load $save --nocine --open rest
& $shot r1 9 --load $save --nocine --open rest --clicks "643:580"
& $shot ch 6 --load $save --nocine --open chapter
& $shot cr 6 --load $save --nocine --open credits
