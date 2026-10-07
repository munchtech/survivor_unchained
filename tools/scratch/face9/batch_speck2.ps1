param([string]$tag = 'sp2', [string]$zoom = '0.62')
# One godot turn after the speckle fix: import (the grain tile, the freckle maps), her bust at the Look, unshaded,
# her neck at the face's close-up, and the book by day and night at 2560x1440: the same frames as sp1.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad\face9'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $TP take godot "face: $tag speckle fixed" --wait 600 | Out-Null
& 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe' --headless --path "$w\godot" --import *> "$sc\logs\import_$tag.log"
$bust = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail', '--zoom', $zoom)
& "$sc\shot.ps1" "${tag}_bust" 8 @bust | Out-Null
& "$sc\shot.ps1" "${tag}_bust_u" 8 @bust --unshaded --no-taa | Out-Null
$face = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--open-eyes', '--hair', 'ponytail')
& "$sc\shot.ps1" "${tag}_face" 8 @face | Out-Null
& "$sc\shot.ps1" "${tag}_face_was" 8 @face --skinparam scatter=0.38 | Out-Null
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--open-eyes')
& "$sc\shotr.ps1" "${tag}_bk_day" 9 '2560x1440' @base --zone verge --time day --open inventory | Out-Null
& "$sc\shotr.ps1" "${tag}_bk_night" 9 '2560x1440' @base --zone verge --time night --open character | Out-Null
python $TP give godot "face: $tag speckle fixed" | Out-Null
"batch $tag done $(Get-Date -Format HH:mm)"
