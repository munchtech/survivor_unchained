param([string]$tag = 'bk0', [switch]$noplay)
# Her face where the player sees it: the book open (Pack, Self, Arts) by day in Lowford and by night in the arena,
# and play zoom from the game's own camera, by day and by night. One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: $tag book shots" --wait 120 | Out-Null
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead')
& "$sc\shot.ps1" "${tag}_pack" 9 @base --zone verge --time day --open inventory | Out-Null
& "$sc\shot.ps1" "${tag}_pack_off" 9 @base --zone verge --time day --open inventory --book-frame off | Out-Null
& "$sc\shot.ps1" "${tag}_self" 9 @base --zone verge --time night --open character | Out-Null
& "$sc\shot.ps1" "${tag}_arts" 9 @base --zone verge --time day --open arts | Out-Null
if (-not $noplay) {
    & "$sc\shot.ps1" "${tag}_play_day" 9 @base --zone arena --auto toward | Out-Null
    & "$sc\shot.ps1" "${tag}_play_night" 9 @base --zone verge --time night --auto toward | Out-Null
    & "$sc\shot.ps1" "${tag}_play_town" 9 @base --zone verge --time day --auto toward | Out-Null
}
python $T give godot "face: $tag book shots" | Out-Null
"book shots $tag done $(Get-Date -Format HH:mm)"
