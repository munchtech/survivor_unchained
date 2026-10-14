# Shipped rig: dark irises with the halved pattern; ears at 40; neck lengths by the neck's scale (front, profile, 40).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$runs = @()
foreach ($f in 'doe', 'sunborn', 'moonlit', 'saffron') { $runs += "$f|$f|" }
foreach ($f in 'own', 'highborn', 'sunborn', 'saffron') { $runs += "${f}_t40|$f|--turn 40" }
foreach ($n in '0', '-1.5', '-3') { $runs += "nk${n}_f|own|--zoom 0.55 --neck-cm $n", "nk${n}_p|own|--zoom 0.55 --turn 90 --neck-cm $n" }
$runs += "nk-1.5_t40|own|--turn 40 --neck-cm -1.5", "nk0_t40|own|--turn 40"
& "$SC\look_ab.ps1" -tag t6 -runs $runs
"T6 DONE $(Get-Date -Format HH:mm)"
