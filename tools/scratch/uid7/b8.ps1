# Batch 8: the old screens as they stand (pause, settings, rest, chapter, credits, creation, the draft), and the notices.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$save = Join-Path $sp 'fortune.json'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot toasts 5.6 --zone verge --nocine --toasts 1.5
& $shot old_pause 6 --load $save --nocine --open pause
& $shot old_settings 6 --load $save --nocine --open pause --clicks "200:520"
& $shot old_rest 6 --load $save --nocine --open rest
& $shot old_chapter 6 --load $save --nocine --open chapter
& $shot old_credits 6 --load $save --nocine --open credits
& $shot old_create 6 --new
& $shot old_draft 9 --zone arena --nocine --open draft
