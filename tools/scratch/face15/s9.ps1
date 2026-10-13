# The four dark irises (Doe chestnut, Sunborn sloe, Moonlit umber, Saffron peat): at the Look, and under neutral light (white rig, grade off).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$runs = @()
foreach ($f in 'doe', 'sunborn', 'moonlit', 'saffron') { $runs += "${f}|$f|", "w_${f}|$f|--rig-white --grade off" }
& "$SC\look_ab.ps1" -tag s9 -runs $runs
"S9 DONE"
