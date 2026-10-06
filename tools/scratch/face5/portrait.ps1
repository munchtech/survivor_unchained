param([string]$id, [string]$ref, [int]$seed = 56, [switch]$skipTrellis)
# One face's portrait target: TRELLIS 2 head of $ref (face4\tr_<id>), then face_wrap.py into
# tools\assets\heroine_face\targets\portrait-<id>.target, with a check sheet (face4\tr_<id>\chk\sheet.jpg).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face5'
$B = 'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
$out = "$sc\tr_$id"
New-Item -ItemType Directory -Force $out | Out-Null
if (-not $skipTrellis) {
    Get-ChildItem $out -Filter '*.glb' -ErrorAction SilentlyContinue | Remove-Item
    python "$w\tools\assets\face_trellis.py" $ref $out --seed $seed *> "$out\trellis.log"
    "[$id] trellis exit $LASTEXITCODE"
}
$shape = (Get-ChildItem $out -Filter 'shape_*.glb' | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
$painted = (Get-ChildItem $out -Filter 'painted_*.glb' | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
& $B -b --python "$w\tools\assets\face_wrap.py" -- $shape $painted "$w\tools\assets\heroine_face\targets\portrait-$id.target" --check "$out\chk" --photo $ref *> "$out\wrap.log"
"[$id] wrap exit $LASTEXITCODE"
Get-Content "$out\wrap.log" | Select-String -Pattern "PLACED|PHOTO|ICP 7|EYE at|TARGET|HAIRLINE|Error|Traceback" | ForEach-Object { "  $($_.Line)" }
$c = "$out\chk"
python "$sc\sheet.py" "$c\sheet.jpg" 360 3 "$c\after_00.png@0.17,0.08,0.83,0.73" "$c\after_35.png@0.17,0.08,0.83,0.73" "$c\after_80.png@0.17,0.08,0.83,0.73" "$c\trellis_00.png@0.17,0.08,0.83,0.73" "$c\trellis_35.png@0.17,0.08,0.83,0.73" "$c\trellis_80.png@0.17,0.08,0.83,0.73" | Out-Null

