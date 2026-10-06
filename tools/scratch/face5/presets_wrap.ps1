param([string[]]$ids = @())
# Each preset's portrait target from its TRELLIS head (face4\tr_<id>), under a blender turn.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$pick = @{ highborn = 'highborn_23'; vixen = 'vixen_23'; doe = 'doe_37'; sunborn = 'sunborn_23'; moonlit = 'moonlit_37';
           saffron = 'saffron_23'; wildling = 'wildling_37'; hardwon = 'hardwon_11'; fey = 'fey_37'; heroine = '../from_face3/refs_her/her_23' }
python $T take blender "face: preset wraps" --wait 30 | Out-Null
foreach ($id in $ids) {
    & "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face5\portrait.ps1" -id $id -ref "$sc\refs_front\$($pick[$id]).png" -skipTrellis
}
python $T give blender "face: preset wraps" | Out-Null

