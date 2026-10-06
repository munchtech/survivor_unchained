param([string[]]$ids = @(), [int]$per = 3)
# TRELLIS heads of the presets' chosen references (face4\refs_front\<pick>.png), $per to a GPU turn, into face4\tr_<id>.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37' }
if (-not $ids.Count) { $ids = @('highborn', 'vixen', 'doe', 'sunborn', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') }
for ($i = 0; $i -lt $ids.Count; $i += $per) {
    python $T take gpu "face: preset TRELLIS heads" --wait 60 | Out-Null
    foreach ($id in $ids[$i..([Math]::Min($i + $per, $ids.Count) - 1)]) {
        $out = "$sc\tr_$id"
        New-Item -ItemType Directory -Force $out | Out-Null
        Get-ChildItem $out -Filter '*.glb' -ErrorAction SilentlyContinue | Remove-Item
        python "$w\tools\assets\face_trellis.py" "$sc\refs_front\$($pick[$id]).png" $out --seed 56 *> "$out\trellis.log"
        "[$id] trellis exit $LASTEXITCODE"
    }
    python $T give gpu "face: preset TRELLIS heads" | Out-Null
}
