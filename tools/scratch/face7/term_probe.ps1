param([string]$tag = 't0', [string[]]$terms = @(''))
# Her skin's terminator (heroine_skin.gdshader `terminator`): the band's view under all the portrait's lights and the
# key alone, for each setting given ('' as the shader has it; '#000000' none). One godot turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: terminator" --wait 120 | Out-Null
$i = 0
foreach ($tv in $terms) {
    $sk = if ($tv) { "terminator=$tv" } else { '' }
    & "$sc\pk.ps1" "${tag}_${i}_all" -noturn -skin $sk -jobs job_clay.json
    & "$sc\pk.ps1" "${tag}_${i}_key" -noturn -skin $sk -lights '1,0,0' -jobs job_clay.json
    $i++
}
python $T give godot "face: terminator" | Out-Null
"terminator $tag done"
