param([string[]]$ids = @('sunborn', 'highborn'), [int]$seed = 61)
# TRELLIS heads again at another seed (one GPU turn), into face4\tr_<id> (the old kept as tr_<id>_s56).
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
python $T take gpu "face: TRELLIS re-rolls" --wait 60 | Out-Null
foreach ($id in $ids) {
    $out = "$sc\tr_$id"
    if (-not (Test-Path "${out}_s56")) { Copy-Item $out "${out}_s56" -Recurse }
    Get-ChildItem $out -Filter '*.glb' -ErrorAction SilentlyContinue | Remove-Item
    python "$w\tools\assets\face_trellis.py" "$sc\refs_front\$($pick[$id]).png" $out --seed $seed *> "$out\trellis.log"
    "[$id] trellis exit $LASTEXITCODE"
}
python $T give gpu "face: TRELLIS re-rolls" | Out-Null
