# One godot turn after merging rendering's grade toe + portrait rig and applying irises_neutral.patch:
# all ten at the Look (irises, under-jaw shade, salmon line, collar sheen), profiles, HerBackSpec A/B, neck lengths
# (Look head-and-shoulders front/profile, in play at 23 and 12).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0'
$TP = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
$godot = 'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe'
$runs = @("own_t80|own|--turn 80", "highborn_t80|highborn|--turn 80", "sunborn_t80|sunborn|--turn 80")
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|" }
foreach ($f in 'highborn', 'doe', 'sunborn') { $runs += "bs1_$f|$f|--skin-set *:back_spec=1", "bs15_$f|$f|--skin-set *:back_spec=0.15" }
foreach ($n in '0', '-1.5', '-3') { $runs += "nk${n}_f|own|--zoom 0.55 --neck-cm $n", "nk${n}_p|own|--zoom 0.55 --turn 90 --neck-cm $n" }
& "$SC\look_ab.ps1" -tag t1 -import -runs $runs
python $TP take godot "face: t1 play" --wait 900 | Out-Null
foreach ($n in '0', '-1.5', '-3') {
    foreach ($c in '23', '12') {
        & "$SC\shot.ps1" "t1_play${c}_nk$n" 10 --quick warden --sex female --zone waystation --time day --cam $c --neck-cm $n
    }
}
python $TP give godot "face: t1 play" | Out-Null
"T1 DONE $(Get-Date -Format HH:mm)"
