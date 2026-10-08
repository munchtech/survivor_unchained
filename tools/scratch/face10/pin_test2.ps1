param([string[]]$ids = @('doe', 'sunborn'), [string[]]$fracs = @('1.0', '0.6'), [string]$tag = 'pz', [string]$detail = '0',
      [string]$angles = '0,35,90', [switch]$noold)
# One blender turn: each face's front warped again from its portrait, its brows and the landmarks round them pinned
# FRAC of the way to the reference's place (heroine_face.py's FACE_BROW_PIN), the sides reused, no Krea unless asked;
# laid; then each paint (and the paint in use, unless -noold) seen lit from round her (preview_lit.py).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\0b33992d-1e38-4eb8-80a1-d5c23b1a44e6\scratchpad\face10'
$in7 = 'C:\Users\munch\Desktop\survivorsunchained_inputs\face7'
$s4 = 'C:\Users\munch\Desktop\survivorsunchained_inputs\face4'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$H = "$w\tools\comfy\out\heroes"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$pick = @{ own = 'her_23'; highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
New-Item -ItemType Directory -Force "$sc\logs", "$sc\lit" | Out-Null
python $T take blender "face: $tag brow pin" --wait 900 | Out-Null
$env:FACE_REUSE = '1'; $env:FACE_DETAIL = $detail; $env:FACE_DETAIL_GAIN = '1.7'; $env:FACE_DETAIL_MM = '2.0'
foreach ($id in $ids) {
    $src = if ($id -eq 'own') { "$in7\paintL" } else { "$in7\paint_$id" }
    $shp = if (Test-Path "$src\shape.json") { "$src\shape.json" } else { '' }
    if (-not $noold) {
        & $B -b "$H\heroine_unpainted.blend" --python "$sc\preview_lit.py" -- "$sc\lit\${id}_old" "$src\face_paint.png" $shp $angles *> "$sc\logs\lit_old.log"
    }
    foreach ($f in $fracs) {
        $out = "$sc\${tag}_${id}_$f"
        if (-not (Test-Path $out)) { Copy-Item $src $out -Recurse }
        if (Test-Path "$out\marks_front.json") { Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("$out\marks_front.json", 'OnlyErrorDialogs', 'SendToRecycleBin') }
        $env:FACE_SHAPE = $shp
        $env:FACE_REF = if ($id -eq 'own') { "$s4\from_face3\refs_her\her_23.png" } else { "$s4\refs_front\$($pick[$id]).png" }
        $env:FACE_BROW_PIN = $f
        & $B -b "$H\heroine_unpainted.blend" --python "$w\tools\assets\heroine_face.py" -- $out *> "$out\pin.log"
        "[$id $f] lay exit $LASTEXITCODE $(Get-Date -Format HH:mm)"
        Get-Content "$out\pin.log" | Select-String -Pattern "Traceback|Error|BROWS|TINTED|FACE PAINT" | Select-Object -Last 5
        & $B -b "$H\heroine_unpainted.blend" --python "$sc\preview_lit.py" -- "$sc\lit\${id}_$f" "$out\face_paint.png" $shp $angles *> "$sc\logs\lit_new.log"
    }
}
$env:FACE_REUSE = ''; $env:FACE_DETAIL = ''; $env:FACE_DETAIL_GAIN = ''; $env:FACE_DETAIL_MM = ''; $env:FACE_REF = ''; $env:FACE_SHAPE = ''; $env:FACE_BROW_PIN = ''
python $T give blender "face: $tag brow pin" | Out-Null
"pin test 2 done $(Get-Date -Format HH:mm)"
