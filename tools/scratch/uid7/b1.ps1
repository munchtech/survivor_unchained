# Batch 1: the map result (cleared, fell, a big haul; 1080 and 1440), the night's result, a loss's
# staging and its toast, the fall's choices, the dial by night at the Waystation.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot mr_clear 11 --zone map --people risen --open mapresult
& $shot mr_fell 11 --zone map --people risen --open mapresult --fell
& $shot mr_many 11 --zone map --people risen --open mapresult --finds 17
& $shot ar_won 11 --zone arena --open result
& $shot fall 22 --night hollow --stage 3 --auto idle --die 10 --choose rise --until 22
& $shot loss 9 --night hollow --stage 3 --auto idle --die 10 --choose letgo --every 0.75 --count 10 --until 60
$env:SHOT_ENGINE = '--fixed-fps 60'
& $shot dial_890 4 --zone waystation --clock 890
& $shot dial_1070 4 --zone waystation --clock 1070
$env:SHOT_RES = '2560x1440'
$env:SHOT_ENGINE = ''
& $shot mr_clear_1440 11 --zone map --people risen --open mapresult
$env:SHOT_ENGINE = '--fixed-fps 60'
& $shot dial_890_1440 4 --zone waystation --clock 890
