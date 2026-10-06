param([string]$tag = 'pz0', [string[]]$extra = @())
# Her face at play zoom, from the game's own camera: the Waystation by day and by night, and an arena's night, walking
# toward the camera. One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: $tag play zoom" --wait 120 | Out-Null
$base = @('--quick', 'warden', '--sex', 'female', '--hair', 'long', '--people', 'dead', '--auto', 'toward') + $extra
& "$sc\shot.ps1" "${tag}_way_day" 9 @base --zone waystation --time day | Out-Null
& "$sc\shot.ps1" "${tag}_way_night" 9 @base --zone waystation --time night | Out-Null
& "$sc\shot.ps1" "${tag}_arena" 9 @base --zone arena | Out-Null
python $T give godot "face: $tag play zoom" | Out-Null
"play zoom $tag done $(Get-Date -Format HH:mm)"
