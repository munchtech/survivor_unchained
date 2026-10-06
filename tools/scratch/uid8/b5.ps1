# Batch 5: line glyphs, the arms, origin and name steps, pause's panels paired, chapter, credits, the title and its notice.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid8'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot n0 7 --new --sex female
& $shot n2 7 --new --sex female --step 2
& $shot n3 7 --new --sex female --step 3
& $shot n4 7 --new --sex female --step 4
& $shot p1 7 --load $save --nocine --open pause --clicks "203:318"
& $shot p2 7 --load $save --nocine --open pause --clicks "211:358"
& $shot ch 7 --load $save --nocine --open chapter
& $shot cr 6 --load $save --nocine --open credits
& $shot adults 6 --adults
