param([string]$tag = 't1', [string[]]$hairs = @('#6e442e', '#7c4a2c', '#8a5030'))
# Her tones (People.HerToneFit) under the white rig, every face, for tone_fit.py; and her hair's colour tried
# (--hair-colour), each under the white rig and the Look's own light. Two godot turns.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
& "$sc\shots_white.ps1" -tag $tag
python $T take godot "face: $tag hair colours" --wait 120 | Out-Null
$base = @('--new', '--sex', 'female', '--step', '1', '--part', '1', '--hair', 'ponytail', '--open-eyes')
$i = 0
foreach ($hx in $hairs) {
    & "$sc\shot.ps1" "${tag}_hair${i}_w" 8 @base --rig-white --hair-colour $hx | Out-Null
    & "$sc\shot.ps1" "${tag}_hair${i}" 8 @base --hair-colour $hx | Out-Null
    $i++
}
python $T give godot "face: $tag hair colours" | Out-Null
"tones and hair $tag done"
