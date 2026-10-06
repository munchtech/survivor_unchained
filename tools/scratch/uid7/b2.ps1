# Batch 2: the results as registers (map: cleared, fell, a big haul; night: won, fell; 1080 and 1440),
# a loss's staging and its held toast, the fall's choices.
$sp = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid7'
$shot = Join-Path $sp 'shot.ps1'
$env:SHOT_ENGINE = ''
$env:SHOT_RES = '1920x1080'
& $shot mr_clear 11 --zone map --people dead --open mapresult
& $shot mr_fell 11 --zone map --people dead --open mapresult --fell
& $shot mr_many 11 --zone map --people dead --open mapresult --finds 17
& $shot ar_won 11 --zone arena --open result
& $shot ar_fell 11 --zone arena --open result --fell
& $shot fall 16 --night hollow --stage 3 --nocine --auto idle --die 10 --choose rise --until 18
& $shot loss 9.5 --night hollow --stage 3 --nocine --auto idle --die 10 --choose letgo --every 0.6 --count 9 --until 50
$env:SHOT_RES = '2560x1440'
& $shot mr_clear_1440 11 --zone map --people dead --open mapresult
& $shot ar_won_1440 11 --zone arena --open result
