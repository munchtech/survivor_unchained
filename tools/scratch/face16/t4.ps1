$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$runs = @()
foreach ($f in 'vixen', 'hardwon', 'fey') { $runs += "$f|$f|" }
$runs += "nk0_f|own|--zoom 0.55", "nk-1.5_f|own|--zoom 0.55 --neck-cm -1.5", "nk-3_f|own|--zoom 0.55 --neck-cm -3", "nk0_p|own|--zoom 0.55 --turn 90", "nk-1.5_p|own|--zoom 0.55 --turn 90 --neck-cm -1.5", "nk-3_p|own|--zoom 0.55 --turn 90 --neck-cm -3"
& "$SC\look_ab.ps1" -tag t4 -runs $runs
"T4 DONE $(Get-Date -Format HH:mm)"
