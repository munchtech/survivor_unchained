# Batch 2: creation rebuilt: the five steps, the look's parts, 1440.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid8'
$shot = Join-Path $sp 'shot.ps1'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot n0 7 --new --sex female
& $shot n1 7 --new --sex female --step 1
& $shot n1b 7 --new --sex female --step 1 --part 1
& $shot n1c 7 --new --sex female --step 1 --part 2
& $shot n2 7 --new --sex female --step 2
& $shot n3 7 --new --sex female --step 3
& $shot n4 7 --new --sex female --step 4
$env:SHOT_RES = '2560x1440'
& $shot n0_1440 7 --new --sex female
