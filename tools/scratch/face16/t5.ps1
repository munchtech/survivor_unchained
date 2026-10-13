# Rig candidate (fill 1/0.98/0.96, bounce 0.09) on all ten; ears repainted; ears at 40; neck lengths by the neck's scale.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$R = '--fill-colour 1,0.98,0.96 --bounce 0.09'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|$R" }
foreach ($f in 'own', 'highborn', 'sunborn', 'saffron') { $runs += "${f}_t40|$f|$R --turn 40" }
$runs += "own_t80|own|$R --turn 80"
foreach ($n in '0', '-1.5', '-3') { $runs += "nk${n}_f|own|$R --zoom 0.55 --neck-cm $n", "nk${n}_p|own|$R --zoom 0.55 --turn 90 --neck-cm $n" }
$runs += "nk-1.5_t40|own|$R --turn 40 --neck-cm -1.5"
& "$SC\look_ab.ps1" -tag t5 -import -runs $runs
"T5 DONE $(Get-Date -Format HH:mm)"
