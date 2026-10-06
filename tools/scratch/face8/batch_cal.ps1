param([string]$tag = 'c1')
# One godot turn: the eye calibration (her irises dyed through greys under the white rig, iris_light 1), the book by
# day with her lamp at three strengths and by night, and play zoom with the far features read at a capped mip.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag calibration" --wait 300 | Out-Null
$cal = 'paint,#0c0c0c,#1a1a1a,#2a2a2a,#3c3c3c,#565656,#787878,#a0a0a0,#c8c8c8'
& "$sc\shot.ps1" "${tag}_eyecal" 8 --new --sex female --step 1 --part 1 --hair ponytail --open-eyes --rig-white --eyecycle $cal --every 1 --count 9 | Out-Null
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--open-eyes')
& "$sc\shot.ps1" "${tag}_bk_day" 9 @base --zone verge --time day --open inventory | Out-Null
& "$sc\shot.ps1" "${tag}_bk_day0" 9 @base --zone verge --time day --open inventory --book-lamp 0 | Out-Null
& "$sc\shot.ps1" "${tag}_bk_day6" 9 @base --zone verge --time day --open inventory --book-lamp 0.6 | Out-Null
& "$sc\shot.ps1" "${tag}_bk_night" 9 @base --zone verge --time night --open character | Out-Null
$pz = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--auto', 'toward')
& "$sc\shot.ps1" "${tag}_pz_day" 9 @pz --zone waystation --time day | Out-Null
& "$sc\shot.ps1" "${tag}_pz_day_b" 9 @pz --zone waystation --time day --skinparam 'far_mip=2,far_bold=2.5' | Out-Null
& "$sc\shot.ps1" "${tag}_pz_night" 9 @pz --zone waystation --time night | Out-Null
& "$sc\shot.ps1" "${tag}_pz_arena" 9 @pz --zone arena | Out-Null
python $TP give godot "face: $tag calibration" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
